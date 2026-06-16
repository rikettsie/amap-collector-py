from unittest.mock import patch
import pytest
import requests
from amap_collector.core.ia44.client import Ia44AmapClient, Ia44AmapClientError
from amap_collector.core.ia44.validations import Ia44ValidationError as ValidationError


class TestClientDepartment:
    def test_default_has_no_department(self) -> None:
        client = Ia44AmapClient()
        assert client._department is None

    def test_department_stored_after_with_department(self) -> None:
        client = Ia44AmapClient().with_department("44")
        assert client._department == "44"


class TestClientValidation:
    def test_invalid_department_raises(self) -> None:
        with pytest.raises(ValidationError):
            Ia44AmapClient().with_department("75")


class TestClientGetAmapList:
    def test_returns_results(self) -> None:
        expected = [{"name": "AMAP Test"}]
        with patch("amap_collector.core.ia44.client.Ia44AmapList") as MockAmapList:
            MockAmapList.return_value.call.return_value = expected
            result = Ia44AmapClient().get_amap_list()
        assert result == expected

    def test_wraps_request_exception_as_client_error(self) -> None:
        with patch("amap_collector.core.ia44.client.Ia44AmapList") as MockAmapList:
            MockAmapList.return_value.call.side_effect = requests.RequestException("timeout")
            with pytest.raises(Ia44AmapClientError):
                Ia44AmapClient().get_amap_list()

    def test_chaining_returns_self(self) -> None:
        client = Ia44AmapClient()
        assert client.with_department("44") is client


class TestClientGetFarmList:
    def test_returns_results(self) -> None:
        expected = [{"name": "Ferme Test"}]
        with patch("amap_collector.core.ia44.client.Ia44FarmList") as MockFarmList:
            MockFarmList.return_value.call.return_value = expected
            result = Ia44AmapClient().get_farm_list()
        assert result == expected

    def test_wraps_request_exception_as_client_error(self) -> None:
        with patch("amap_collector.core.ia44.client.Ia44FarmList") as MockFarmList:
            MockFarmList.return_value.call.side_effect = requests.RequestException("timeout")
            with pytest.raises(Ia44AmapClientError):
                Ia44AmapClient().get_farm_list()
