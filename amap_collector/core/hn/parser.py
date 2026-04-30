import re
import json
from typing import Any


class HnAmapListParser:

    def parse(self, html: str) -> list[dict[str, Any]]:
        scripts = re.findall(r'self\.__next_f\.push\(\[1,(.*?)\]\s*\)', html, re.DOTALL)
        if not scripts:
            return []

        inner = json.loads(max(scripts, key=len))

        idx = inner.find('"amaps":[')
        if idx == -1:
            return []

        m = re.search(r'"amaps":(\[.*)', inner[idx:], re.DOTALL)
        if not m:
            return []

        arr_str = self.__extract_array(m.group(1))
        # RSC back-references (e.g. "$5:1:props:...") are not valid JSON values
        arr_str = re.sub(r'"\$[^"]*"', 'null', arr_str)

        raw: list[Any] = json.loads(arr_str)
        return [self.__normalize(a) for a in raw if isinstance(a, dict) and a.get('__typename') == 'Amap']

    def __extract_array(self, s: str) -> str:
        depth = 0
        for i, c in enumerate(s):
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return s[:i + 1]
        return s

    def __normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        delivery = item.get('delivery') or {}
        open_days = [
            {
                'week_day': d.get('weekDay', ''),
                'open_hour': d.get('openHour', ''),
                'close_hour': d.get('closeHour', ''),
            }
            for d in (delivery.get('openDays') or [])
            if isinstance(d, dict)
        ]
        products = [
            {'name': p.get('name', ''), 'category': p.get('category', '')}
            for p in (item.get('products') or [])
            if isinstance(p, dict) and p.get('__typename') == 'Product'
        ]
        farms = [
            {
                'id': f.get('id', ''),
                'slug': f.get('slug', ''),
                'name': f.get('name', ''),
                'city': (((f.get('contacts') or {}).get('address') or {}).get('city') or '').strip(),
            }
            for f in (item.get('farms') or [])
            if isinstance(f, dict) and f.get('__typename') == 'Farm'
        ]

        return {
            'id': item.get('id', ''),
            'slug': item.get('slug', ''),
            'name': item.get('name', ''),
            'status': None,
            'abstract': item.get('abstract'),
            'delivery': {
                'place_name': None,
                'address': self.__format_address(delivery.get('address') or {}),
                'days': open_days,
                'basket_count': delivery.get('basketCount'),
            },
            'contact_address': self.__format_address((item.get('contacts') or {}).get('address') or {}),
            'comment': None,
            'products': products,
            'farms': farms,
        }

    def __format_address(self, addr: dict[str, Any]) -> str:
        parts = [
            (addr.get('name') or '').strip(),
            (addr.get('street') or '').strip(),
            (addr.get('zipcode') or '').strip(),
            (addr.get('city') or '').strip(),
            (addr.get('country') or '').strip(),
        ]
        return " ".join(parts).strip()


class HnAmapDetailParser:

    def parse(self, html: str) -> dict[str, Any]:
        scripts = re.findall(r'self\.__next_f\.push\(\[1,(.*?)\]\s*\)', html, re.DOTALL)
        for s in scripts:
            inner = json.loads(s)
            if '"children":"Contact"' not in inner:
                continue
            m = re.search(
                r'"children"\s*:\s*"Contact"\s*\}.*?"children"\s*:\s*\["\$","div".*?"children"\s*:\s*(\[)',
                inner, re.DOTALL
            )
            if not m:
                continue
            arr_str = self.__extract_balanced(inner, m.start(1))
            children = json.loads(arr_str)
            return self.__parse_children(children)
        return {}

    def __extract_balanced(self, s: str, start: int) -> str:
        depth = 0
        for i, c in enumerate(s[start:]):
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return s[start:start + i + 1]
        return s[start:]

    def __parse_children(self, children: list[Any]) -> dict[str, Any]:
        name = email = phone = website = ''
        for item in children:
            if not isinstance(item, list):
                continue
            if len(item) >= 4 and item[1] == 'strong':
                props = item[3] if isinstance(item[3], dict) else {}
                name = (props.get('children') or '').strip()
            elif len(item) == 2 and isinstance(item[0], str):
                text = item[0].strip()
                if '@' in text:
                    email = text
                elif text.startswith('http') or text.startswith('www'):
                    website = text
                elif text:
                    phone = text
        return {
            'name': name,
            'emails': [email] if email else [],
            'phones': [phone] if phone else [],
            'website': website,
        }


class HnFarmDetailParser(HnAmapDetailParser):
    """Farm detail pages share the same RSC contact-block structure as AMAP detail pages."""


class HnFarmListParser:

    def parse(self, html: str) -> list[dict[str, Any]]:
        scripts = re.findall(r'self\.__next_f\.push\(\[1,(.*?)\]\s*\)', html, re.DOTALL)
        if not scripts:
            return []

        inner = json.loads(max(scripts, key=len))

        idx = inner.find('"farms":[')
        if idx == -1 or inner[idx - 1] != '{':
            return []

        m = re.search(r'"farms":(\[.*)', inner[idx:], re.DOTALL)
        if not m:
            return []

        arr_str = self.__extract_array(m.group(1))
        arr_str = re.sub(r'"\$[^"]*"', 'null', arr_str)

        raw: list[Any] = json.loads(arr_str)
        return [self.__normalize(f) for f in raw if isinstance(f, dict) and f.get('__typename') == 'Farm']

    def __extract_array(self, s: str) -> str:
        depth = 0
        for i, c in enumerate(s):
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return s[:i + 1]
        return s

    def __normalize(self, farm: dict[str, Any]) -> dict[str, Any]:
        addr = ((farm.get('contacts') or {}).get('address') or {})
        products = [
            {'name': p.get('name', ''), 'category': p.get('category', '')}
            for p in (farm.get('products') or [])
            if isinstance(p, dict) and p.get('__typename') == 'Product'
        ]
        return {
            'id': (farm.get('id') or ''),
            'slug': (farm.get('slug') or ''),
            'name': (farm.get('name') or ''),
            'address': self.__format_address(addr),
            'city': (addr.get('city') or '').strip(),
            'products': products,
        }
    
    def __format_address(self, addr: dict[str, Any]) -> str:
        parts = [
            (addr.get('name') or '').strip(),
            (addr.get('street') or '').strip(),
            (addr.get('zipcode') or '').strip(),
            (addr.get('city') or '').strip(),
            (addr.get('country') or '').strip(),
        ]
        return " ".join(parts).strip()
