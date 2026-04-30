from unittest.mock import MagicMock, patch
import pytest
import requests
from amap_collector.core.whole.endpoint import WholeAmapList


def _patch_all(dept_url: str | None = "amap,cher,18.html", list_items: list | None = None):
    index_mock = MagicMock()
    index_mock.find_dept_url.return_value = dept_url

    list_mock = MagicMock()
    list_mock.parse.return_value = list_items or []

    return (
        patch("amap_collector.core.whole.endpoint.requests.get"),
        patch("amap_collector.core.whole.endpoint.requests.head"),
        patch("amap_collector.core.whole.endpoint.WholeIndexParser", return_value=index_mock),
        patch("amap_collector.core.whole.endpoint.WholeAmapListParser", return_value=list_mock),
    )


def _item(name: str = "AMAP Test", **kwargs) -> dict:
    base = {
        "id": "",
        "name": name,
        "emails": [],
        "raw_websites": [],
        "products": [],
        "distribution": "",
        "phones": [],
    }
    return {**base, **kwargs}


class TestWholeAmapList:
    def test_returns_empty_when_dept_not_found(self) -> None:
        p1, p2, p3, p4 = _patch_all(dept_url=None)
        with p1, p2, p3, p4:
            result = WholeAmapList().call({"department": "18"})
        assert result == []

    def test_returns_empty_when_no_amaps(self) -> None:
        p1, p2, p3, p4 = _patch_all(list_items=[])
        with p1, p2, p3, p4:
            result = WholeAmapList().call({"department": "18"})
        assert result == []

    def test_basic_amap_returned(self) -> None:
        item = _item("AMAP Test", emails=["test@amap.fr"], products=["légumes"], distribution="Vendredi 18h-19h")
        p1, p2, p3, p4 = _patch_all(list_items=[item])
        with p1, p2, p3, p4:
            result = WholeAmapList().call({"department": "18"})
        assert len(result) == 1
        assert result[0]["name"] == "AMAP Test"
        assert result[0]["contact"]["emails"] == ["test@amap.fr"]
        assert result[0]["products"] == [{"name": "légumes", "category": ""}]
        assert result[0]["comment"] == "Vendredi 18h-19h"

    def test_id_from_parser_used_when_present(self) -> None:
        p1, p2, p3, p4 = _patch_all(list_items=[_item(id="1914")])
        with p1, p2, p3, p4:
            result = WholeAmapList().call({"department": "18"})
        assert result[0]["id"] == "1914"

    def test_id_generated_from_name_when_parser_id_empty(self) -> None:
        p1, p2, p3, p4 = _patch_all(list_items=[_item("AMAP Les Graines", id="")])
        with p1, p2, p3, p4:
            result = WholeAmapList().call({"department": "18"})
        assert result[0]["id"] == "amap-les-graines"

    def test_phones_passed_to_contact(self) -> None:
        item = _item(phones=["06 12 34 56 78"])
        p1, p2, p3, p4 = _patch_all(list_items=[item])
        with p1, p2, p3, p4:
            result = WholeAmapList().call({"department": "18"})
        assert result[0]["contact"]["phones"] == ["06 12 34 56 78"]

    def test_relative_website_href_resolved_with_base_uri(self) -> None:
        item = _item(raw_websites=["go.php?typ=1&id=1914"])
        p1, p2, p3, p4 = _patch_all(list_items=[item])
        with p1, p2 as mock_head, p3, p4:
            mock_head.return_value.url = "http://amap-bourges.fr/contact.html"
            result = WholeAmapList().call({"department": "18"})
        # Should have called head with the absolute URL
        called_url = mock_head.call_args[0][0]
        assert called_url.startswith("https://www.avenir-bio.fr/")
        assert result[0]["website"] == "http://amap-bourges.fr/contact.html"

    def test_absolute_website_href_not_prefixed(self) -> None:
        item = _item(raw_websites=["https://fr-fr.facebook.com/example/"])
        p1, p2, p3, p4 = _patch_all(list_items=[item])
        with p1, p2 as mock_head, p3, p4:
            mock_head.return_value.url = "https://fr-fr.facebook.com/example/"
            _result = WholeAmapList().call({"department": "18"})
        called_url = mock_head.call_args[0][0]
        assert called_url == "https://fr-fr.facebook.com/example/"

    def test_website_fallback_on_request_error(self) -> None:
        item = _item(raw_websites=["go.php?typ=1&id=1914"])
        p1, p2, p3, p4 = _patch_all(list_items=[item])
        with p1, p2 as mock_head, p3, p4:
            mock_head.side_effect = requests.RequestException("timeout")
            result = WholeAmapList().call({"department": "18"})
        # Falls back to the absolute URL (relative href + base)
        assert result[0]["website"].startswith("https://www.avenir-bio.fr/")

    def test_empty_website_when_no_raw_websites(self) -> None:
        p1, p2, p3, p4 = _patch_all(list_items=[_item()])
        with p1, p2 as mock_head, p3, p4:
            result = WholeAmapList().call({"department": "18"})
        assert result[0]["website"] == ""
        mock_head.assert_not_called()

    def test_empty_distribution_gives_none_comment(self) -> None:
        p1, p2, p3, p4 = _patch_all(list_items=[_item(distribution="")])
        with p1, p2, p3, p4:
            result = WholeAmapList().call({"department": "18"})
        assert result[0]["comment"] is None

    def test_output_shape(self) -> None:
        p1, p2, p3, p4 = _patch_all(list_items=[_item()])
        with p1, p2, p3, p4:
            result = WholeAmapList().call({"department": "18"})
        entry = result[0]
        assert entry["status"] is None
        assert entry["abstract"] is None
        assert entry["farms"] == []
        assert entry["delivery"]["basket_count"] is None
        assert entry["delivery"]["days"] == []

    def test_raises_on_http_error(self) -> None:
        with patch("amap_collector.core.whole.endpoint.requests.get") as mock_get, \
             patch("amap_collector.core.whole.endpoint.requests.head"), \
             patch("amap_collector.core.whole.endpoint.WholeIndexParser"), \
             patch("amap_collector.core.whole.endpoint.WholeAmapListParser"):
            mock_get.return_value.raise_for_status.side_effect = requests.HTTPError()
            with pytest.raises(requests.HTTPError):
                WholeAmapList().call({"department": "18"})
