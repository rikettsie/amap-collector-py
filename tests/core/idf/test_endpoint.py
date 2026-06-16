from unittest.mock import MagicMock, patch
import pytest
import requests
from amap_collector.core.idf.endpoint import IdfAmapList, ZipCodeInfo


class TestZipCodeInfo:
    def test_returns_parsed_json(self) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": "75019", "centre": {"coordinates": [2.38, 48.88]}}
        with patch("amap_collector.core.idf.endpoint.requests.get", return_value=mock_response):
            result = ZipCodeInfo().call("75019")
        assert result["code"] == "75019"

    def test_returns_empty_dict_on_http_error(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        with patch("amap_collector.core.idf.endpoint.requests.get", return_value=mock_response):
            result = ZipCodeInfo().call("00000")
        assert result == {}

    def test_returns_empty_dict_on_connection_error(self) -> None:
        with patch("amap_collector.core.idf.endpoint.requests.get", side_effect=requests.ConnectionError()):
            result = ZipCodeInfo().call("75019")
        assert result == {}


class TestAmapList:
    def test_call_returns_parsed_results(self) -> None:
        mock_response = MagicMock()
        mock_response.text = "<div class='liste-fiches liste-fiches-amaps'></div>"
        mock_session = MagicMock()
        mock_session.post.return_value = mock_response

        amap = IdfAmapList()
        amap._session = mock_session

        with patch.object(amap, "_ensure_session", return_value=mock_session):
            result = amap.call({"departement": "75"})

        assert result == []

    def test_call_retries_on_request_exception(self) -> None:
        bad_response = MagicMock()
        bad_response.raise_for_status.side_effect = requests.HTTPError()

        good_response = MagicMock()
        good_response.text = "<div class='liste-fiches liste-fiches-amaps'></div>"

        mock_session = MagicMock()
        mock_session.post.side_effect = [bad_response, good_response]

        amap = IdfAmapList()
        with patch.object(amap, "_ensure_session", return_value=mock_session):
            result = amap.call({"departement": "75"})

        assert mock_session.post.call_count == 2
        assert result == []

    def test_call_raises_if_retry_also_fails(self) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_session = MagicMock()
        mock_session.post.return_value = mock_response

        amap = IdfAmapList()
        with patch.object(amap, "_ensure_session", return_value=mock_session):
            with pytest.raises(requests.HTTPError):
                amap.call({"departement": "75"})
