from unittest.mock import MagicMock, patch
import pytest
import requests
from amap_scraper.core.client import AmapClient, AmapClientError
from amap_scraper.core.validations import ValidationError


class TestClientPayload:
    def test_default_payload(self) -> None:
        client = AmapClient()
        payload = client._AmapClient__payload()
        assert payload["recherche"] == "amap"
        assert payload["departement"] == "75"
        assert payload["km_autour"] == "2"
        assert "cp" not in payload

    def test_payload_with_department(self) -> None:
        client = AmapClient().with_department("92")
        assert client._AmapClient__payload()["departement"] == "92"

    def test_payload_with_km_radius(self) -> None:
        client = AmapClient().with_km_radius("10")
        assert client._AmapClient__payload()["km_autour"] == "10"

    def test_payload_with_zip_code(self) -> None:
        with patch("amap_scraper.core.validations.ZipCodeInfo") as MockZip:
            MockZip.return_value.call.return_value = {"code": "75019"}
            client = AmapClient().with_zip_code("75019")
        assert client._AmapClient__payload()["cp"] == "75019"



class TestClientValidation:
    def test_invalid_department_raises(self) -> None:
        with pytest.raises(ValidationError):
            AmapClient().with_department("99")

    def test_invalid_radius_raises(self) -> None:
        with pytest.raises(ValidationError):
            AmapClient().with_km_radius("3")



class TestClientGetAmapList:
    def test_returns_results(self) -> None:
        expected = [{"name": "AMAP Test"}]
        with patch("amap_scraper.core.client.AmapList") as MockAmapList:
            MockAmapList.return_value.call.return_value = expected
            result = AmapClient().get_amap_list()
        assert result == expected

    def test_wraps_request_exception_as_client_error(self) -> None:
        with patch("amap_scraper.core.client.AmapList") as MockAmapList:
            MockAmapList.return_value.call.side_effect = requests.RequestException("timeout")
            with pytest.raises(AmapClientError):
                AmapClient().get_amap_list()

    def test_chaining_returns_self(self) -> None:
        client = AmapClient()
        assert client.with_department("92").with_km_radius("5") is client
