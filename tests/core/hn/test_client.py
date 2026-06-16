from unittest.mock import patch
import pytest
import requests
from amap_collector.core.hn.client import HnAmapClient, HnAmapClientError
from amap_collector.core.hn.validations import HnValidationError as ValidationError


class TestClientPayload:
    def test_default_payload_has_no_department(self) -> None:
        client = HnAmapClient()
        payload = client._payload()
        assert payload["department"] is None

    def test_payload_with_department(self) -> None:
        client = HnAmapClient().with_department("76")
        assert client._payload()["department"] == "76"


class TestClientValidation:
    def test_invalid_department_raises(self) -> None:
        with pytest.raises(ValidationError):
            HnAmapClient().with_department("75")


class TestClientGetAmapList:
    def test_returns_results(self) -> None:
        expected = [{"name": "AMAP Test"}]
        with patch("amap_collector.core.hn.client.HnAmapList") as MockAmapList:
            MockAmapList.return_value.call.return_value = expected
            result = HnAmapClient().get_amap_list()
        assert result == expected

    def test_wraps_request_exception_as_client_error(self) -> None:
        with patch("amap_collector.core.hn.client.HnAmapList") as MockAmapList:
            MockAmapList.return_value.call.side_effect = requests.RequestException("timeout")
            with pytest.raises(HnAmapClientError):
                HnAmapClient().get_amap_list()

    def test_chaining_returns_self(self) -> None:
        client = HnAmapClient()
        assert client.with_department("27") is client


class TestClientGetFarmList:
    def test_returns_results(self) -> None:
        expected = [{"name": "Ferme Test"}]
        with patch("amap_collector.core.hn.client.HnFarmList") as MockFarmList:
            MockFarmList.return_value.call.return_value = expected
            result = HnAmapClient().get_farm_list()
        assert result == expected

    def test_wraps_request_exception_as_client_error(self) -> None:
        with patch("amap_collector.core.hn.client.HnFarmList") as MockFarmList:
            MockFarmList.return_value.call.side_effect = requests.RequestException("timeout")
            with pytest.raises(HnAmapClientError):
                HnAmapClient().get_farm_list()
