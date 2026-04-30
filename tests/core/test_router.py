import pytest

from amap_collector.core.router import AmapClientBuilder, AmapClientBuilderError
from amap_collector.core.idf.client import IdfAmapClient, IDF_CLIENT_LABEL
from amap_collector.core.hn.client import HnAmapClient, HN_CLIENT_LABEL
from amap_collector.core.ia44.client import Ia44AmapClient, IA44_CLIENT_LABEL
from amap_collector.core.whole.client import WholeAmapClient, WHOLE_CLIENT_LABEL


IDF_DEPTS = ["75", "77", "78", "91", "92", "93", "94", "95"]
HN_DEPTS = ["27", "76"]
IA44_DEPTS = ["44"]
WHOLE_DEPTS = ["01", "13", "31", "33", "69"]
INVALID_DEPTS = ["02", "96"]


class TestClientLabel:
    @pytest.mark.parametrize("dept", IDF_DEPTS)
    def test_idf_departments_map_to_idf_label(self, dept: str) -> None:
        assert AmapClientBuilder(dept).target()["label"] == IDF_CLIENT_LABEL

    @pytest.mark.parametrize("dept", HN_DEPTS)
    def test_hn_departments_map_to_hn_label(self, dept: str) -> None:
        assert AmapClientBuilder(dept).target()["label"] == HN_CLIENT_LABEL

    @pytest.mark.parametrize("dept", IA44_DEPTS)
    def test_ia44_departments_map_to_ia44_label(self, dept: str) -> None:
        assert AmapClientBuilder(dept).target()["label"] == IA44_CLIENT_LABEL

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

    def test_ia44_department_returns_ia44_client(self) -> None:
        assert isinstance(AmapClientBuilder("44").get_client(), Ia44AmapClient)

    def test_whole_department_returns_whole_client(self) -> None:
        assert isinstance(AmapClientBuilder("01").get_client(), WholeAmapClient)


class TestSupportsMethods:
    def test_supports_farm_list_for_hn(self) -> None:
        assert AmapClientBuilder("76").supports_farm_list() is True

    def test_supports_farm_list_for_ia44(self) -> None:
        assert AmapClientBuilder("44").supports_farm_list() is True

    def test_supports_farm_list_for_idf(self) -> None:
        assert AmapClientBuilder("75").supports_farm_list() is False

    def test_supports_farm_list_for_whole(self) -> None:
        assert AmapClientBuilder("01").supports_farm_list() is False

    def test_supports_km_radius_for_idf(self) -> None:
        assert AmapClientBuilder("75").supports_km_radius() is True

    def test_supports_km_radius_for_hn(self) -> None:
        assert AmapClientBuilder("76").supports_km_radius() is False

    def test_supports_km_radius_for_whole(self) -> None:
        assert AmapClientBuilder("01").supports_km_radius() is False

    def test_supports_zip_code_for_idf(self) -> None:
        assert AmapClientBuilder("75").supports_zip_code() is True

    def test_supports_zip_code_for_hn(self) -> None:
        assert AmapClientBuilder("76").supports_zip_code() is False

    def test_supports_zip_code_for_whole(self) -> None:
        assert AmapClientBuilder("01").supports_zip_code() is False
