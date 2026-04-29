from unittest.mock import patch
import pytest
import requests
from amap_collector.core.idf.client import IdfAmapClient, IdfAmapClientError
from amap_collector.core.idf.validations import IdfValidationError as ValidationError


class TestClientPayload:
    def test_default_payload(self) -> None:
        client = IdfAmapClient()
        payload = client._IdfAmapClient__payload()
        assert payload["recherche"] == "amap"
        assert payload["departement"] == "75"
        assert payload["km_autour"] == "2"
        assert "cp" not in payload

    def test_payload_with_department(self) -> None:
        client = IdfAmapClient().with_department("92")
        assert client._IdfAmapClient__payload()["departement"] == "92"

    def test_payload_with_km_radius(self) -> None:
        client = IdfAmapClient().with_km_radius("10")
        assert client._IdfAmapClient__payload()["km_autour"] == "10"

    def test_payload_with_zip_code(self) -> None:
        with patch("amap_collector.core.idf.validations.ZipCodeInfo") as MockZip:
            MockZip.return_value.call.return_value = {"features": [{"properties": {"postcode": "75019"}}]}
            client = IdfAmapClient().with_zip_code("75019")
        assert client._IdfAmapClient__payload()["cp"] == "75019"


class TestClientValidation:
    def test_invalid_department_raises(self) -> None:
        with pytest.raises(ValidationError):
            IdfAmapClient().with_department("99")

    def test_invalid_radius_raises(self) -> None:
        with pytest.raises(ValidationError):
            IdfAmapClient().with_km_radius("3")


class TestClientGetAmapList:
    def test_returns_results(self) -> None:
        expected = [{"name": "AMAP Test"}]
        with patch("amap_collector.core.idf.client.IdfAmapList") as MockAmapList:
            MockAmapList.return_value.call.return_value = expected
            result = IdfAmapClient().get_amap_list()
        assert result == expected

    def test_wraps_request_exception_as_client_error(self) -> None:
        with patch("amap_collector.core.idf.client.IdfAmapList") as MockAmapList:
            MockAmapList.return_value.call.side_effect = requests.RequestException("timeout")
            with pytest.raises(IdfAmapClientError):
                IdfAmapClient().get_amap_list()

    def test_chaining_returns_self(self) -> None:
        client = IdfAmapClient()
        assert client.with_department("92").with_km_radius("5") is client
