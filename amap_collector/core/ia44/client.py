from typing import Optional, Self
import requests

import amap_collector.core.ia44.validations as validations
from amap_collector.core.ia44.endpoint import Ia44AmapList, Ia44FarmList

IA44_CLIENT_LABEL: str = 'ia44'


class Ia44AmapClientError(RuntimeError):
    """Raised when an HTTP error occurs while fetching AMAP data."""


class Ia44AmapClient:

    def __init__(self) -> None:
        self._department: Optional[str] = None

    def with_department(self, department: str) -> Self:
        self._department = validations.validate_department(department)
        return self

    def get_amap_list(self) -> list[dict]:
        try:
            return Ia44AmapList().call()
        except requests.RequestException as err:
            raise Ia44AmapClientError(err)

    def get_farm_list(self) -> list[dict]:
        try:
            return Ia44FarmList().call()
        except requests.RequestException as err:
            raise Ia44AmapClientError(err)
