from typing import Optional, Self
import requests

import core.validations as validations
from core.endpoint import AmapList

class ClientError(RuntimeError):
    pass

class Client:

    def __init__(self) -> None:
        self.__department: Optional[str] = None   # `departement` param
        self.__km_radius: Optional[str] = None    # `km_autour` param
        self.__zip_code: Optional[str] = None     # `cp` param
        self.__latitude: Optional[str] = None     # `lat` param
        self.__longitude: Optional[str] = None    # `lng` param

    def with_department(self, department: str) -> Self:
        self.__department = validations.validate_department(department)
        return self

    def with_km_radius(self, km_radius: str) -> Self:
        self.__km_radius = validations.validate_km_radius(km_radius)
        return self
    
    def with_zip_code(self, zip_code: str) -> Self:
        self.__zip_code = validations.validate_zip_code(zip_code)
        return self
    
    def with_coordinates(self, latitude: str, longitude: str) -> Self:
        coords = validations.validate_coordinates(latitude, longitude)
        self.__latitude, self.__longitude = coords
        return self


    def get_amap_list(self) -> list[dict[str, str]]:
        try:
            return AmapList().call(self.__payload())
        except requests.RequestException as err:
            raise ClientError(err)


    def __payload(self) -> dict[str, str]:
        pl: dict[str, str] = {"recherche": "amap"}

        pl["departement"] = self.__department if self.__department else validations.DEFAULT_DEPT
        pl["km_autour"] = self.__km_radius if self.__km_radius else validations.DEFAULT_RADIUS

        if self.__zip_code:
            pl["cp"] = self.__zip_code

        if self.__latitude and self.__longitude:
            pl["lat"] = self.__latitude
            pl["lng"] = self.__longitude

        return pl
