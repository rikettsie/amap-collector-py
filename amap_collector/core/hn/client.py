from typing import Optional, Self
import requests

import amap_collector.core.hn.validations as validations
from amap_collector.core.hn.endpoint import HnAmapList

HN_CLIENT_LABEL: str = 'hn'

class HnAmapClientError(RuntimeError):
    """Raised when an HTTP error occurs while fetching AMAP data."""


class HnAmapClient:
    """Client for querying the AMAP Haute-Normandie directory.

    Exposes a fluent interface to set search parameters before fetching results.

    Example:
        results = HnAmapClient().with_department("93").get_amap_list()
    """

    def __init__(self) -> None:
        self.__department: Optional[str] = None

    def with_department(self, department: str) -> Self:
        """Set the department code to search in.

        Args:
            department: Supported codes: 27, 76.

        Returns:
            The client instance for chaining.

        Raises:
            HnValidationError: If the department code is not supported.
        """
        self.__department = validations.validate_department(department)
        return self

    def get_amap_list(self) -> list[dict[str, str]]:
        """Fetch the list of AMAPs matching the configured parameters.

        Returns:
            A list of AMAP entries. Each entry is a dict with keys:
            ``name``, ``status``, ``website``, ``contact``, ``delivery``,
            ``comment`` and other minor fields.

        Raises:
            HnAmapClientError: If the HTTP request fails.
        """
        try:
            return HnAmapList().call(self.__payload())
        except requests.RequestException as err:
            raise HnAmapClientError(err)


    def __payload(self) -> dict[str, Optional[str]]:
        return {"department": self.__department}
