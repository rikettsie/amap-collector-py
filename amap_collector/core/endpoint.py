import requests
from typing import Optional, Any
from amap_collector.core.parser import AmapListParser

class AmapList:
    BASE_URI: str = "https://amap-idf.org"
    AMAP_LIST_PATH: str = "les-amap/trouver-une-amap-en-idf"
    HEADERS: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Referer": f"{BASE_URI}/{AMAP_LIST_PATH}",
    }

    def __init__(self) -> None:
        self.__uri: str = f"{self.BASE_URI}/{self.AMAP_LIST_PATH}"
        self.__session: Optional[requests.Session] = None

    def __ensure_session(self, force: bool = False) -> requests.Session:
        if force or not self.__session:
            session = requests.Session()
            session.headers.update(self.HEADERS)
            session.get(self.__uri)
            self.__session = session
        return self.__session

    def call(self, data: dict[str, str]) -> list[dict[str, Any]]:
        session = self.__ensure_session()
        try:
            ret = session.post(self.__uri, data=data)
            ret.raise_for_status()
        except requests.RequestException:
            session = self.__ensure_session(force=True)
            ret = session.post(self.__uri, data=data)
            ret.raise_for_status()

        return AmapListParser().parse(ret.text)


class ZipCodeInfo:
    BASE_URI: str = "https://geo.api.gouv.fr/communes"

    def call(self, zip_code: str) -> dict[str, Any]:
        try:
            ret = requests.get(f"{self.BASE_URI}/{zip_code}/?fields=centre&format=json")
            ret.raise_for_status()
            return ret.json()
        except requests.RequestException:
            return {}
