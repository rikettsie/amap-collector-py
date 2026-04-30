import re
from typing import Any

from bs4 import BeautifulSoup, Tag


class WholeIndexParser:
    def find_dept_url(self, html: str, dept: str) -> str | None:
        soup = BeautifulSoup(html, 'html.parser')
        area_map = soup.find('map', {'name': 'fr'})
        if not area_map:
            return None
        for area in area_map.find_all('area'):
            href = str(area.get('href', ''))
            m = re.match(r'amap,[\w-]+,([^.]+)\.html', href)
            if m and self.__depts_match(dept, m.group(1)):
                return href
        return None

    def __depts_match(self, a: str, b: str) -> bool:
        try:
            return int(a) == int(b)
        except ValueError:
            return a.upper() == b.upper()


class WholeAmapListParser:
    def parse(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        # Both FDG1 and FDG2 are valid AMAP card variants
        cards = soup.select('.col-md-6.TL.PTB20b')
        return [r for card in cards if (r := self.__parse_card(card)) is not None]

    def __parse_card(self, card: Tag) -> dict[str, Any] | None:
        name = self.__parse_name(card)
        if not name:
            return None
        return {
            'id': self.__parse_id(card),
            'name': name,
            'emails': self.__parse_emails(card),
            'raw_websites': self.__parse_raw_websites(card),
            'products': self.__parse_products(card),
            'distribution': self.__parse_distribution(card),
            'phones': self.__parse_phones(card),
        }

    def __parse_id(self, card: Tag) -> str:
        a = card.find('a', href=re.compile(r'fiche_amap,'))
        if a:
            m = re.search(r'fiche_amap,[\w-]+,(\d+)\.html', str(a['href']))
            if m:
                return m.group(1)
        return ''

    def __parse_name(self, card: Tag) -> str:
        center = card.find('center')
        if not center:
            return ''
        strong = center.find('strong')
        if not strong:
            return ''
        # Name is in an <a> link when present; city follows as a bare text node
        a = strong.find('a')
        if a:
            return a.get_text(strip=True)
        # No link: full text is "NAME à CITY" — strip the city suffix
        text = strong.get_text(strip=True)
        idx = text.rfind(' à ')
        return text[:idx].strip() if idx != -1 else text

    def __parse_emails(self, card: Tag) -> list[str]:
        emails = []
        for a in card.find_all('a', href=True):
            href = str(a['href'])
            if href.startswith('mailto:'):
                email = href[7:]
                if email:
                    emails.append(email)
        return emails

    def __parse_raw_websites(self, card: Tag) -> list[str]:
        # Website link is an <a> wrapping <span class="Tredb">Site Internet</span>
        for div in card.find_all('div', style=True):
            if 'height:30px' in str(div.get('style', '')).replace(' ', ''):
                for a in div.find_all('a', href=True):
                    span = a.find('span')
                    if span and 'site internet' in span.get_text(strip=True).lower():
                        return [str(a['href'])]
        return []

    def __parse_products(self, card: Tag) -> list[str]:
        for div in card.find_all('div', style=True):
            if 'height:80px' in str(div.get('style', '')).replace(' ', ''):
                text = div.get_text(separator=' ', strip=True)
                m = re.search(r'Produits\s*:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
                if m:
                    return [p.strip() for p in m.group(1).split(',') if p.strip()]
        return []

    def __parse_distribution(self, card: Tag) -> str:
        for div in card.find_all('div', style=True):
            if 'height:110px' in str(div.get('style', '')).replace(' ', ''):
                text = div.get_text(separator=' ', strip=True)
                m = re.search(
                    r'Distribution\s+(.+?)(?:\s*Contact\s+t|\Z)',
                    text, re.IGNORECASE | re.DOTALL
                )
                if m:
                    return m.group(1).strip()
        return ''

    def __parse_phones(self, card: Tag) -> list[str]:
        for div in card.find_all('div', style=True):
            if 'height:110px' in str(div.get('style', '')).replace(' ', ''):
                text = div.get_text(separator=' ', strip=True)
                m = re.search(r'Contact\s+t[^:]*:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
                if m:
                    return re.findall(
                        r'0\d[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
                        m.group(1)
                    )
        return []
