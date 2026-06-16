import requests
from typing import Optional, Any
from amap_collector.core.idf.parser import IdfAmapListParser

class IdfAmapList:
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
        self._session: Optional[requests.Session] = None

    def _ensure_session(self, force: bool = False) -> requests.Session:
        if force or not self._session:
            session = requests.Session()
            session.headers.update(self.HEADERS)
            session.get(self.__uri)
            self._session = session
        return self._session

    def call(self, data: dict[str, str]) -> list[dict[str, Any]]:
        session = self._ensure_session()
        try:
            ret = session.post(self.__uri, data=data)
            ret.raise_for_status()
        except requests.RequestException:
            session = self._ensure_session(force=True)
            ret = session.post(self.__uri, data=data)
            ret.raise_for_status()

        return IdfAmapListParser().parse(ret.text)


class ZipCodeInfo:
    BASE_URI: str = "https://api-adresse.data.gouv.fr"

    def call(self, zip_code: str) -> dict[str, Any]:
        try:
            ret = requests.get(f"{self.BASE_URI}/search/?q={zip_code}&postcode={zip_code}&limit=1")
            ret.raise_for_status()
            return ret.json()
        except requests.RequestException:
            return {}
