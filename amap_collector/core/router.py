from functools import cache
from typing import Optional, Any

from amap_collector.core.idf.validations import ALLOWED_DEPTS as IDF_DEPTS
from amap_collector.core.hn.validations import ALLOWED_DEPTS as HN_DEPTS
from amap_collector.core.ia44.validations import ALLOWED_DEPTS as IA44_DEPTS
from amap_collector.core.idf.client import IdfAmapClient, IDF_CLIENT_LABEL
from amap_collector.core.hn.client import HnAmapClient, HN_CLIENT_LABEL
from amap_collector.core.ia44.client import Ia44AmapClient, IA44_CLIENT_LABEL
from amap_collector.core.whole.client import WholeAmapClient, WHOLE_CLIENT_LABEL


@cache
def allowed_depts() -> list[str]:
    depts: list[str] = ["2A", "2B"]

    for dint in range(95):
        dstr = str(dint+1)
        if dstr == "2":
            continue
        dstr = f"0{dstr}" if len(dstr) == 1 else dstr
        depts.append(dstr)

    return depts


class AmapClientBuilderError(RuntimeError):
    pass


class AmapClientBuilder:

    def __init__(self, code: str) -> None:
        self.__validate_code(code)
        self.__target_zip_code: Optional[str] = code if self.__is_zipcode(code) else None

        dept: str = code[0:2]
        self.__validate_department(dept)
        self.__target_dept: str = dept

        self.__client_label: str = self.__region_client_mapper()

    def target(self) -> dict[str, Optional[str]]:
        return {
            "label": self.__client_label,
            "dept": self.__target_dept,
            "zip_code": self.__target_zip_code
        }

    def get_client(self) -> Any:
        if self.__client_label == IDF_CLIENT_LABEL:
            return IdfAmapClient()
        elif self.__client_label == HN_CLIENT_LABEL:
            return HnAmapClient()
        elif self.__client_label == IA44_CLIENT_LABEL:
            return Ia44AmapClient()
        else:
            return WholeAmapClient()

    def is_idf(self) -> bool:
        return self.__client_label == IDF_CLIENT_LABEL

    def __region_client_mapper(self) -> str:
        if self.__target_dept in IDF_DEPTS:
            return IDF_CLIENT_LABEL
        elif self.__target_dept in HN_DEPTS:
            return HN_CLIENT_LABEL
        elif self.__target_dept in IA44_DEPTS:
            return IA44_CLIENT_LABEL
        else:
            return WHOLE_CLIENT_LABEL

    def __validate_code(self, code: str) -> None:
        if not (self.__is_department(code) or self.__is_zipcode(code)):
            raise AmapClientBuilderError(
                f"Code must be a department (2 digits) or a zip code of 5 digits, but {code} was given"
            )

    def __validate_department(self, dept: str) -> None:
        if dept not in allowed_depts():
            raise AmapClientBuilderError(f"Allowed departments are {allowed_depts()}, but {dept} was given")

    def __is_zipcode(self, code: str) -> bool:
        return len(code) == 5

    def __is_department(self, code: str) -> bool:
        return len(code) == 2
