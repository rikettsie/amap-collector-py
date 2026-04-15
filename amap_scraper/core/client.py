from typing import Optional, Self
import requests

import amap_scraper.core.validations as validations
from amap_scraper.core.endpoint import AmapList

class AmapClientError(RuntimeError):
    """Raised when an HTTP error occurs while fetching AMAP data."""


class AmapClient:
    """Client for querying the AMAP Île-de-France directory.

    Exposes a fluent interface to set search parameters before fetching results.

    Example:
        results = AmapClient().with_department("93").with_km_radius("10").get_amap_list()
    """

    def __init__(self) -> None:
        self.__department: Optional[str] = None   # `departement` param
        self.__km_radius: Optional[str] = None    # `km_autour` param
        self.__zip_code: Optional[str] = None     # `cp` param

    def with_department(self, department: str) -> Self:
        """Set the department code to search in.

        Args:
            department: Supported codes: 75, 77, 78, 91, 92, 93, 94, 95.

        Returns:
            The client instance for chaining.

        Raises:
            ValidationError: If the department code is not supported.
        """
        self.__department = validations.validate_department(department)
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
        self.__km_radius = validations.validate_km_radius(km_radius)
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
        self.__zip_code = validations.validate_zip_code(zip_code)
        return self

    def get_amap_list(self) -> list[dict[str, str]]:
        """Fetch the list of AMAPs matching the configured parameters.

        Returns:
            A list of AMAP entries. Each entry is a dict with keys:
            ``name``, ``status``, ``website``, ``contact``, ``place``,
            and ``comment``.

        Raises:
            AmapClientError: If the HTTP request fails.
        """
        try:
            return AmapList().call(self.__payload())
        except requests.RequestException as err:
            raise AmapClientError(err)


    def __payload(self) -> dict[str, str]:
        pl: dict[str, str] = {"recherche": "amap"}

        pl["departement"] = self.__department if self.__department else validations.DEFAULT_DEPT
        pl["km_autour"] = self.__km_radius if self.__km_radius else validations.DEFAULT_RADIUS

        if self.__zip_code:
            pl["cp"] = self.__zip_code

        return pl
