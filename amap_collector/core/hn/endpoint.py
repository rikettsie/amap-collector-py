import requests
from typing import Any

from amap_collector.core.hn.parser import HnAmapListParser, HnAmapDetailParser, HnFarmDetailParser, HnFarmListParser


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

    def call(self, data: dict[str, str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        amap_list_parser = HnAmapListParser()
        amap_detail_parser = HnAmapDetailParser()
        farm_detail_parser = HnFarmDetailParser()
        page = 1

        while True:
            ret = requests.get(self.__list_uri, params={"page": page}, headers=self.HEADERS)

            if ret.status_code == requests.codes.not_found:
                break
            ret.raise_for_status()

            page_items = amap_list_parser.parse(ret.text)
            new_items = []
            for item in page_items:
                if item['id'] not in seen_ids and self.__is_in_department(item, data["department"]):
                    new_items.append(item)
                    seen_ids.add(item['id'])
            if not new_items:
                break

            results.extend(new_items)
            page += 1

        for item in results:
            # enriching root AMAP item
            amap_slug = item.pop('slug', '')
            amap_detail = self.__fetch_amap_detail(amap_slug, amap_detail_parser) if amap_slug else {}
            item['website'] = amap_detail.get('website', '')
            item['contact'] = {
                'name': amap_detail.get('name', ''),
                'emails': amap_detail.get('emails', []),
                'phones': amap_detail.get('phones', []),
            }

            # enriching farm item
            for farm in item['farms']:
                farm_detail = self.__fetch_farm_detail(farm['slug'], farm_detail_parser) if farm['slug'] else {}
                farm['website'] = farm_detail.get('website', '')
                farm['contact'] = {
                    'name': farm_detail.get('name', ''),
                    'emails': farm_detail.get('emails', []),
                    'phones': farm_detail.get('phones', []),
                }
                farm['protocols'] = {}

        return results

    def __is_in_department(self, item: dict[str, Any], dept: str) -> bool:
        if addr := item["delivery"]["address"]:
            found_dept: str = addr.split()[-2][0:2]
            return found_dept == dept
        else:
            return False

    def __fetch_amap_detail(self, slug: str, parser: HnAmapDetailParser) -> dict[str, Any]:
        uri = f"{self.BASE_URI}/amap/{slug}"
        ret = requests.get(uri, headers=self.HEADERS)
        ret.raise_for_status()
        return parser.parse(ret.text)

    def __fetch_farm_detail(self, slug: str, parser: HnFarmDetailParser) -> dict[str, Any]:
        uri = f"{self.BASE_URI}/ferme/{slug}"
        ret = requests.get(uri, headers=self.HEADERS)
        ret.raise_for_status()
        return parser.parse(ret.text)


class HnFarmList:
    BASE_URI: str = "https://reseau-amap-hn.com"
    FARM_LIST_PATH: str = "fermes"
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }

    def __init__(self) -> None:
        self.__list_uri: str = f"{self.BASE_URI}/{self.FARM_LIST_PATH}"

    def call(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        list_parser = HnFarmListParser()
        detail_parser = HnFarmDetailParser()
        page = 1

        while True:
            ret = requests.get(self.__list_uri, params={"page": page}, headers=self.HEADERS)
            if ret.status_code == requests.codes.not_found:
                break
            ret.raise_for_status()

            page_items = list_parser.parse(ret.text)
            new_items = [i for i in page_items if i['id'] and i['id'] not in seen_ids]
            if not new_items:
                break

            for item in new_items:
                seen_ids.add(item['id'])
            results.extend(new_items)
            page += 1

        for farm in results:
            slug = farm.pop('slug', '')
            farm_detail = self.__fetch_detail(slug, detail_parser) if slug else {}
            farm['website'] = farm_detail.get('website', '')
            farm['contact'] = {
                'name': farm_detail.get('name', ''),
                'emails': farm_detail.get('emails', []),
                'phones': farm_detail.get('phones', []),
            }
            farm['protocols'] = {}

        return results

    def __fetch_detail(self, slug: str, parser: HnFarmDetailParser) -> dict[str, Any]:
        uri = f"{self.BASE_URI}/ferme/{slug}"
        ret = requests.get(uri, headers=self.HEADERS)
        ret.raise_for_status()
        return parser.parse(ret.text)
