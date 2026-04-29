import pytest

from amap_collector.core.router import AmapClientBuilder, AmapClientBuilderError
from amap_collector.core.idf.client import IdfAmapClient, IDF_CLIENT_LABEL
from amap_collector.core.hn.client import HnAmapClient, HN_CLIENT_LABEL
from amap_collector.core.whole.client import WholeAmapClient, WHOLE_CLIENT_LABEL


IDF_DEPTS = ["75", "77", "78", "91", "92", "93", "94", "95"]
HN_DEPTS = ["27", "76"]
WHOLE_DEPTS = ["01", "13", "31", "33", "69"]
INVALID_DEPTS = ["02", "96"]


class TestClientLabel:
    @pytest.mark.parametrize("dept", IDF_DEPTS)
    def test_idf_departments_map_to_idf_label(self, dept: str) -> None:
        assert AmapClientBuilder(dept).target()["label"] == IDF_CLIENT_LABEL

    @pytest.mark.parametrize("dept", HN_DEPTS)
    def test_hn_departments_map_to_hn_label(self, dept: str) -> None:
        assert AmapClientBuilder(dept).target()["label"] == HN_CLIENT_LABEL

    @pytest.mark.parametrize("dept", WHOLE_DEPTS)
    def test_other_departments_map_to_whole_label(self, dept: str) -> None:
        assert AmapClientBuilder(dept).target()["label"] == WHOLE_CLIENT_LABEL


class TestInvalidDepartment:
    @pytest.mark.parametrize("dept", INVALID_DEPTS)
    def test_non_existent_department_raises(self, dept: str) -> None:
        with pytest.raises(AmapClientBuilderError):
            AmapClientBuilder(dept)


class TestGetClient:
    def test_idf_department_returns_idf_client(self) -> None:
        assert isinstance(AmapClientBuilder("75").get_client(), IdfAmapClient)

    def test_hn_department_returns_hn_client(self) -> None:
        assert isinstance(AmapClientBuilder("27").get_client(), HnAmapClient)

    def test_whole_department_returns_whole_client(self) -> None:
        assert isinstance(AmapClientBuilder("01").get_client(), WholeAmapClient)
