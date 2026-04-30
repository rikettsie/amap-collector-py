import re
import requests
from typing import Any

from amap_collector.core.whole.parser import WholeIndexParser, WholeAmapListParser


class WholeAmapList:
    BASE_URI: str = "https://www.avenir-bio.fr"
    INDEX_PATH: str = "/annuaire_amap.php"
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }

    def call(self, data: dict[str, str]) -> list[dict[str, Any]]:
        dept = data["department"]
        index_parser = WholeIndexParser()
        list_parser = WholeAmapListParser()

        ret = requests.get(f"{self.BASE_URI}{self.INDEX_PATH}", headers=self.HEADERS)
        ret.raise_for_status()

        dept_path = index_parser.find_dept_url(ret.text, dept)
        if not dept_path:
            return []

        ret = requests.get(f"{self.BASE_URI}/{dept_path}", headers=self.HEADERS)
        ret.raise_for_status()

        items = list_parser.parse(ret.text)
        results: list[dict[str, Any]] = []

        for item in items:
            resolved_websites = [
                self.__resolve_url(href)
                for href in item.get('raw_websites', [])
            ]
            results.append({
                'id': item.get('id') or self.__make_id(item['name']),
                'name': item['name'],
                'status': None,
                'abstract': None,
                'contact_address': '',
                'comment': item.get('distribution') or None,
                'products': [{'name': p, 'category': ''} for p in item.get('products', [])],
                'delivery': {
                    'place_name': None,
                    'address': '',
                    'days': [],
                    'basket_count': None,
                },
                'website': resolved_websites[0] if resolved_websites else '',
                'contact': {
                    'name': '',
                    'emails': item.get('emails', []),
                    'phones': item.get('phones', []),
                },
                'farms': [],
            })

        return results

    def __resolve_url(self, href: str) -> str:
        url = href if href.startswith('http') else f"{self.BASE_URI}/{href}"
        try:
            ret = requests.head(url, allow_redirects=True, headers=self.HEADERS, timeout=10)
            return ret.url
        except requests.RequestException:
            return url

    def __make_id(self, name: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
