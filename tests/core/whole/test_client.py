from unittest.mock import patch
import pytest
import requests
from amap_collector.core.whole.client import WholeAmapClient, WholeAmapClientError
from amap_collector.core.whole.validations import WholeValidationError


class TestClientPayload:
    def test_default_payload_has_no_department(self) -> None:
        client = WholeAmapClient()
        assert client._payload()["department"] is None

    def test_payload_with_department(self) -> None:
        client = WholeAmapClient().with_department("18")
        assert client._payload()["department"] == "18"


class TestClientValidation:
    def test_invalid_department_raises(self) -> None:
        with pytest.raises(WholeValidationError):
            WholeAmapClient().with_department("75")

    def test_valid_department_accepted(self) -> None:
        client = WholeAmapClient().with_department("18")
        assert client._payload()["department"] == "18"


class TestClientGetAmapList:
    def test_returns_results(self) -> None:
        expected = [{"name": "AMAP Test"}]
        with patch("amap_collector.core.whole.client.WholeAmapList") as MockAmapList:
            MockAmapList.return_value.call.return_value = expected
            result = WholeAmapClient().get_amap_list()
        assert result == expected

    def test_wraps_request_exception_as_client_error(self) -> None:
        with patch("amap_collector.core.whole.client.WholeAmapList") as MockAmapList:
            MockAmapList.return_value.call.side_effect = requests.RequestException("timeout")
            with pytest.raises(WholeAmapClientError):
                WholeAmapClient().get_amap_list()

    def test_chaining_returns_self(self) -> None:
        client = WholeAmapClient()
        assert client.with_department("18") is client
