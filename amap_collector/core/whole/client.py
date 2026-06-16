from typing import Optional, Self
import requests

import amap_collector.core.whole.validations as validations
from amap_collector.core.whole.endpoint import WholeAmapList

WHOLE_CLIENT_LABEL: str = 'whole'


class WholeAmapClientError(RuntimeError):
    """Raised when an HTTP error occurs while fetching AMAP data."""


class WholeAmapClient:
    def __init__(self) -> None:
        self._department: Optional[str] = None

    def with_department(self, department: str) -> Self:
        self._department = validations.validate_department(department)
        return self

    def get_amap_list(self) -> list[dict]:
        try:
            return WholeAmapList().call(self._payload())
        except requests.RequestException as err:
            raise WholeAmapClientError(err)

    def _payload(self) -> dict[str, Optional[str]]:
        return {"department": self._department}
