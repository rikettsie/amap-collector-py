import requests
from typing import Any

from amap_collector.core.ia44.parser import (
    Ia44AmapListParser,
    Ia44AmapDetailParser,
    Ia44FarmerDetailParser,
)


class Ia44AmapList:
    BASE_URI: str = "https://www.amap44.org"
    LIST_PATH: str = "/?s=&category=258&location=&a=true"
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }

    def call(self) -> list[dict[str, Any]]:
        list_parser = Ia44AmapListParser()
        detail_parser = Ia44AmapDetailParser()
        farm_detail_parser = Ia44FarmerDetailParser()

        results = self.__fetch_all_amaps(list_parser)

        for item in results:
            slug = item.pop('slug')
            item.pop('category_hrefs', None)

            detail = self.__fetch_detail(slug, detail_parser)
            farmer_list_url = detail.pop('farmer_list_url', None)
            products_raw = detail.pop('products', [])

            item['id'] = slug
            item['status'] = None
            item['abstract'] = detail.get('abstract') or item.get('abstract') or None
            item['delivery'] = {
                'place_name': None,
                'address': detail.get('address') or item.pop('address', ''),
                'days': detail.get('days', []),
                'basket_count': None,
            }
            item['contact_address'] = detail.get('address') or ''
            item.pop('address', None)
            item['comment'] = None
            item['products'] = [{'name': p, 'category': ''} for p in products_raw]
            item['website'] = detail.get('website') or item.pop('website', '')
            item['contact'] = {
                'name': '',
                'emails': detail.get('emails', []),
                'phones': [],
            }

            item['farms'] = self.__fetch_farms(
                farmer_list_url, list_parser, farm_detail_parser
            ) if farmer_list_url else []

        return results

    def __fetch_all_amaps(self, parser: Ia44AmapListParser) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        seen_slugs: set[str] = set()
        page = 1

        while True:
            url = f"{self.BASE_URI}{self.LIST_PATH}&paged={page}"
            ret = requests.get(url, headers=self.HEADERS)
            ret.raise_for_status()

            page_items = parser.parse(ret.text)
            new_items = [i for i in page_items if i['slug'] and i['slug'] not in seen_slugs]
            if not new_items:
                break

            seen_slugs.update(i['slug'] for i in new_items)
            results.extend(new_items)
            page += 1

        return results

    def __fetch_detail(self, slug: str, parser: Ia44AmapDetailParser) -> dict[str, Any]:
        url = f"{self.BASE_URI}/?ait-item={slug}"
        ret = requests.get(url, headers=self.HEADERS)
        ret.raise_for_status()
        return parser.parse(ret.text)

    def __fetch_farms(
        self,
        farmer_list_url: str,
        list_parser: Ia44AmapListParser,
        farm_detail_parser: Ia44FarmerDetailParser,
    ) -> list[dict[str, Any]]:
        try:
            ret = requests.get(farmer_list_url, headers=self.HEADERS)
            ret.raise_for_status()
        except requests.RequestException:
            return []

        # The location-specific list contains mixed items (AMAPs + farmers).
        # Keep only non-AMAP items (farmers, fishers, etc.) identified by the
        # absence of the "amap" category slug.
        all_cards = list_parser.parse(ret.text)
        farmer_cards = [
            c for c in all_cards
            if not any('ait-items=amap' in h for h in c.get('category_hrefs', []))
            and c['slug']
        ]

        farms: list[dict[str, Any]] = []
        seen: set[str] = set()
        for card in farmer_cards:
            farm_slug = card['slug']
            if farm_slug in seen:
                continue
            seen.add(farm_slug)

            try:
                farm_url = f"{self.BASE_URI}/?ait-item={farm_slug}"
                ret = requests.get(farm_url, headers=self.HEADERS)
                ret.raise_for_status()
                farm_detail = farm_detail_parser.parse(ret.text)
            except requests.RequestException:
                farm_detail = {}

            farms.append({
                'id': farm_slug,
                'slug': farm_slug,
                'name': card.get('name') or farm_detail.get('name', ''),
                'city': farm_detail.get('city', ''),
                'website': farm_detail.get('website', '') or card.get('website', ''),
                'contact': {
                    'name': '',
                    'emails': farm_detail.get('emails', []),
                    'phones': [],
                },
                'protocols': farm_detail.get('protocols', {}),
            })

        return farms


class Ia44FarmList:
    BASE_URI: str = "https://www.amap44.org"
    FARM_LIST_PATH: str = "/?ait-items=paysan"
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }

    def call(self) -> list[dict[str, Any]]:
        list_parser = Ia44AmapListParser()
        detail_parser = Ia44FarmerDetailParser()

        cards = self.__fetch_all_farms(list_parser)

        results: list[dict[str, Any]] = []
        for card in cards:
            slug = card['slug']
            detail = self.__fetch_detail(slug, detail_parser)
            results.append({
                'id': slug,
                'name': card.get('name') or detail.get('name', ''),
                'city': detail.get('city', ''),
                'website': detail.get('website', '') or card.get('website', ''),
                'contact': {
                    'name': '',
                    'emails': detail.get('emails', []),
                    'phones': [],
                },
                'protocols': detail.get('protocols', {}),
            })

        return results

    def __fetch_all_farms(self, parser: Ia44AmapListParser) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        seen_slugs: set[str] = set()
        page = 1

        while True:
            url = f"{self.BASE_URI}{self.FARM_LIST_PATH}&paged={page}"
            ret = requests.get(url, headers=self.HEADERS)
            ret.raise_for_status()

            page_items = parser.parse(ret.text)
            new_items = [i for i in page_items if i['slug'] and i['slug'] not in seen_slugs]
            if not new_items:
                break

            seen_slugs.update(i['slug'] for i in new_items)
            results.extend(new_items)
            page += 1

        return results

    def __fetch_detail(self, slug: str, parser: Ia44FarmerDetailParser) -> dict[str, Any]:
        url = f"{self.BASE_URI}/?ait-item={slug}"
        ret = requests.get(url, headers=self.HEADERS)
        ret.raise_for_status()
        return parser.parse(ret.text)
