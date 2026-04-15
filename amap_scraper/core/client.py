from typing import Optional, Self
import requests

import amap_scraper.core.validations as validations
from amap_scraper.core.endpoint import AmapList

class AmapClientError(RuntimeError):
    pass

class AmapClient:

    def __init__(self) -> None:
        self.__department: Optional[str] = None   # `departement` param
        self.__km_radius: Optional[str] = None    # `km_autour` param
        self.__zip_code: Optional[str] = None     # `cp` param
    def with_department(self, department: str) -> Self:
        self.__department = validations.validate_department(department)
        return self

    def with_km_radius(self, km_radius: str) -> Self:
        self.__km_radius = validations.validate_km_radius(km_radius)
        return self
    
    def with_zip_code(self, zip_code: str) -> Self:
        self.__zip_code = validations.validate_zip_code(zip_code)
        return self
    
    def get_amap_list(self) -> list[dict[str, str]]:
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
