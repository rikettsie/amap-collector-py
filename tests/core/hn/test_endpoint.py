from unittest.mock import MagicMock, patch
import pytest
import requests
from amap_collector.core.hn.endpoint import HnAmapList


def _list_item(id: str, dept: str, slug: str = "s", farms: list | None = None) -> dict:
    return {
        "id": id,
        "slug": slug,
        "name": f"AMAP {id}",
        "status": None,
        "abstract": None,
        "delivery": {
            "place_name": None,
            "address": f"1 rue X, {dept}000, CITY",
            "days": [],
            "basket_count": 0,
        },
        "contact_address": "",
        "comment": None,
        "products": [],
        "farms": farms or [],
    }


def _patch_all(list_items_per_page, detail_result=None, farm_result=None):
    """Context manager that patches all three parsers and requests.get."""
    list_parser_mock = MagicMock()
    list_parser_mock.parse.side_effect = list_items_per_page

    detail_parser_mock = MagicMock()
    detail_parser_mock.parse.return_value = detail_result or {}

    farm_parser_mock = MagicMock()
    farm_parser_mock.parse.return_value = farm_result or {}

    return (
        patch("amap_collector.core.hn.endpoint.requests.get"),
        patch("amap_collector.core.hn.endpoint.HnAmapListParser", return_value=list_parser_mock),
        patch("amap_collector.core.hn.endpoint.HnAmapDetailParser", return_value=detail_parser_mock),
        patch("amap_collector.core.hn.endpoint.HnFarmDetailParser", return_value=farm_parser_mock),
    )


class TestHnAmapList:
    def test_returns_empty_when_first_page_is_empty(self) -> None:
        with patch("amap_collector.core.hn.endpoint.requests.get"), \
             patch("amap_collector.core.hn.endpoint.HnAmapListParser") as MockList, \
             patch("amap_collector.core.hn.endpoint.HnAmapDetailParser"), \
             patch("amap_collector.core.hn.endpoint.HnFarmDetailParser"):
            MockList.return_value.parse.return_value = []
            result = HnAmapList().call({"department": "76"})
        assert result == []

    def test_pagination_stops_when_all_ids_seen(self) -> None:
        item = _list_item("1", "76", "slug-1")
        p1, p2, p3, p4 = _patch_all([[item], [item]])
        with p1, p2 as MockList, p3, p4:
            result = HnAmapList().call({"department": "76"})
        assert MockList.return_value.parse.call_count == 2
        assert len(result) == 1

    def test_department_filter_excludes_wrong_dept(self) -> None:
        item_76 = _list_item("1", "76", "slug-76")
        item_27 = _list_item("2", "27", "slug-27")
        p1, p2, p3, p4 = _patch_all([[item_76, item_27], [item_76, item_27]])
        with p1, p2, p3, p4:
            result = HnAmapList().call({"department": "76"})
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_amap_slug_not_in_result(self) -> None:
        item = _list_item("1", "76", "slug-1")
        p1, p2, p3, p4 = _patch_all([[item], [item]])
        with p1, p2, p3, p4:
            result = HnAmapList().call({"department": "76"})
        assert "slug" not in result[0]

    def test_contact_merged_from_detail(self) -> None:
        item = _list_item("1", "76", "slug-1")
        detail = {"name": "Jean", "emails": ["j@x.fr"], "phones": ["06 00"], "website": "https://x.fr"}
        p1, p2, p3, p4 = _patch_all([[item], [item]], detail_result=detail)
        with p1, p2, p3, p4:
            result = HnAmapList().call({"department": "76"})
        assert result[0]["contact"] == {"name": "Jean", "emails": ["j@x.fr"], "phones": ["06 00"]}
        assert result[0]["website"] == "https://x.fr"

    def test_farm_contact_merged(self) -> None:
        farm = {"id": "f1", "slug": "farm-slug", "name": "Farm", "city": "City"}
        item = _list_item("1", "76", "slug-1", farms=[farm])
        farm_detail = {"name": "Fermier", "emails": ["f@farm.fr"], "phones": [], "website": "https://farm.fr"}
        p1, p2, p3, p4 = _patch_all([[item], [item]], farm_result=farm_detail)
        with p1, p2, p3, p4:
            result = HnAmapList().call({"department": "76"})
        f = result[0]["farms"][0]
        assert f["website"] == "https://farm.fr"
        assert f["contact"] == {"name": "Fermier", "emails": ["f@farm.fr"], "phones": []}

    def test_raises_on_http_error(self) -> None:
        with patch("amap_collector.core.hn.endpoint.requests.get") as mock_get, \
             patch("amap_collector.core.hn.endpoint.HnAmapListParser"), \
             patch("amap_collector.core.hn.endpoint.HnAmapDetailParser"), \
             patch("amap_collector.core.hn.endpoint.HnFarmDetailParser"):
            mock_get.return_value.raise_for_status.side_effect = requests.HTTPError()
            with pytest.raises(requests.HTTPError):
                HnAmapList().call({"department": "76"})
