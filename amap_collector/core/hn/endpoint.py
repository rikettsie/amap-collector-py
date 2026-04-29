import requests
from typing import Any

from amap_collector.core.hn.parser import HnAmapListParser, HnAmapDetailParser


class HnAmapList:
    BASE_URI: str = "https://reseau-amap-hn.com"
    AMAP_LIST_PATH: str = "amaps"
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }

    def __init__(self) -> None:
        self.__list_uri: str = f"{self.BASE_URI}/{self.AMAP_LIST_PATH}"

    def call(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        list_parser = HnAmapListParser()
        detail_parser = HnAmapDetailParser()
        page = 1

        while True:
            ret = requests.get(self.__list_uri, params={"page": page}, headers=self.HEADERS)
            ret.raise_for_status()

            page_items = list_parser.parse(ret.text)
            new_items = [item for item in page_items if item['id'] not in seen_ids]
            if not new_items:
                break

            seen_ids.update(item['id'] for item in new_items)
            results.extend(new_items)
            page += 1

        for item in results:
            slug = item.pop('slug', '')
            detail = self.__fetch_detail(slug, detail_parser) if slug else {}
            item['website'] = detail.get('website', '')
            item['contact'] = {
                'name': detail.get('name', ''),
                'emails': detail.get('emails', []),
                'phones': detail.get('phones', []),
            }

        return results

    def __fetch_detail(self, slug: str, parser: HnAmapDetailParser) -> dict[str, Any]:
        uri = f"{self.BASE_URI}/amap/{slug}"
        ret = requests.get(uri, headers=self.HEADERS)
        ret.raise_for_status()
        return parser.parse(ret.text)
