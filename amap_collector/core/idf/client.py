from typing import Optional, Self
import requests

import amap_collector.core.idf.validations as validations
from amap_collector.core.idf.endpoint import IdfAmapList

IDF_CLIENT_LABEL: str = 'idf'

class IdfAmapClientError(RuntimeError):
    """Raised when an HTTP error occurs while fetching AMAP data."""


class IdfAmapClient:
    """Client for querying the AMAP Île-de-France directory.

    Exposes a fluent interface to set search parameters before fetching results.

    Example:
        results = IdfAmapClient().with_department("93").with_km_radius("10").get_amap_list()
    """

    def __init__(self) -> None:
        self._department: Optional[str] = None   # `departement` param
        self._km_radius: Optional[str] = None    # `km_autour` param
        self._zip_code: Optional[str] = None     # `cp` param

    def with_department(self, department: str) -> Self:
        """Set the department code to search in.

        Args:
            department: Supported codes: 75, 77, 78, 91, 92, 93, 94, 95.

        Returns:
            The client instance for chaining.

        Raises:
            IdfValidationError: If the department code is not supported.
        """
        self._department = validations.validate_department(department)
        return self

    def with_km_radius(self, km_radius: str) -> Self:
        """Set the search radius around the target location.

        Args:
            km_radius: Radius in km. Supported values: 2, 5, 10, 15, 20.

        Returns:
            The client instance for chaining.

        Raises:
            ValidationError: If the radius value is not supported.
        """
        self._km_radius = validations.validate_km_radius(km_radius)
        return self

    def with_zip_code(self, zip_code: str) -> Self:
        """Set a French zip code to search around.

        When specified, overrides the department parameter entirely.

        Args:
            zip_code: A valid French zip code (e.g. ``"75012"``).

        Returns:
            The client instance for chaining.

        Raises:
            ValidationError: If the zip code is not recognised.
        """
        self._zip_code = validations.validate_zip_code(zip_code)
        return self

    def get_amap_list(self) -> list[dict[str, str]]:
        """Fetch the list of AMAPs matching the configured parameters.

        Returns:
            A list of AMAP entries. Each entry is a dict with keys:
            ``name``, ``status``, ``website``, ``contact``, ``delivery``,
            ``comment`` and other minor fields.

        Raises:
            IdfAmapClientError: If the HTTP request fails.
        """
        try:
            return IdfAmapList().call(self._payload())
        except requests.RequestException as err:
            raise IdfAmapClientError(err)


    def _payload(self) -> dict[str, str]:
        pl: dict[str, str] = {"recherche": "amap"}

        pl["departement"] = self._department if self._department else validations.DEFAULT_DEPT
        pl["km_autour"] = self._km_radius if self._km_radius else validations.DEFAULT_RADIUS

        if self._zip_code:
            pl["cp"] = self._zip_code

        return pl
