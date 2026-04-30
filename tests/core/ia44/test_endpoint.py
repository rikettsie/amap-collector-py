from unittest.mock import MagicMock, patch
import pytest
import requests
from amap_collector.core.ia44.endpoint import Ia44AmapList, Ia44FarmList

_EMPTY_DETAIL: dict = {
    'abstract': None, 'address': '', 'days': [],
    'emails': [], 'website': '', 'products': [], 'farmer_list_url': None,
}


def _card(slug: str, name: str = "AMAP Test", has_amap_cat: bool = False) -> dict:
    return {
        'slug': slug,
        'name': name,
        'abstract': None,
        'address': '1 rue Test, 44000 NANTES',
        'website': '',
        'category_hrefs': ['?ait-items=amap'] if has_amap_cat else ['?ait-items=producteur'],
    }


def _patch_all(list_side_effects, detail_result=None, farm_detail_result=None):
    list_mock = MagicMock()
    list_mock.parse.side_effect = list_side_effects

    detail_mock = MagicMock()
    detail_mock.parse.return_value = detail_result or _EMPTY_DETAIL.copy()

    farm_mock = MagicMock()
    farm_mock.parse.return_value = farm_detail_result or {}

    return (
        patch("amap_collector.core.ia44.endpoint.requests.get"),
        patch("amap_collector.core.ia44.endpoint.Ia44AmapListParser", return_value=list_mock),
        patch("amap_collector.core.ia44.endpoint.Ia44AmapDetailParser", return_value=detail_mock),
        patch("amap_collector.core.ia44.endpoint.Ia44FarmerDetailParser", return_value=farm_mock),
    )


class TestIa44AmapList:
    def test_returns_empty_when_first_page_is_empty(self) -> None:
        p1, p2, p3, p4 = _patch_all([[]])
        with p1, p2, p3, p4:
            result = Ia44AmapList().call()
        assert result == []

    def test_pagination_stops_when_all_slugs_seen(self) -> None:
        card = _card("amap-01")
        p1, p2, p3, p4 = _patch_all([[card], [card]])
        with p1, p2 as MockList, p3, p4:
            result = Ia44AmapList().call()
        assert MockList.return_value.parse.call_count == 2
        assert len(result) == 1

    def test_slug_not_in_result(self) -> None:
        card = _card("amap-01")
        p1, p2, p3, p4 = _patch_all([[card], [card]])
        with p1, p2, p3, p4:
            result = Ia44AmapList().call()
        assert "slug" not in result[0]

    def test_category_hrefs_not_in_result(self) -> None:
        card = _card("amap-01")
        p1, p2, p3, p4 = _patch_all([[card], [card]])
        with p1, p2, p3, p4:
            result = Ia44AmapList().call()
        assert "category_hrefs" not in result[0]

    def test_id_set_from_slug(self) -> None:
        card = _card("amap-01")
        p1, p2, p3, p4 = _patch_all([[card], [card]])
        with p1, p2, p3, p4:
            result = Ia44AmapList().call()
        assert result[0]["id"] == "amap-01"

    def test_detail_address_preferred_over_list_address(self) -> None:
        card = _card("amap-01")
        detail = {**_EMPTY_DETAIL, 'address': '5 rue Détail, 44000 NANTES'}
        p1, p2, p3, p4 = _patch_all([[card], [card]], detail_result=detail)
        with p1, p2, p3, p4:
            result = Ia44AmapList().call()
        assert result[0]["delivery"]["address"] == "5 rue Détail, 44000 NANTES"

    def test_contact_from_detail(self) -> None:
        card = _card("amap-01")
        detail = {**_EMPTY_DETAIL, 'emails': ['contact@test.example'], 'website': 'https://test.example'}
        p1, p2, p3, p4 = _patch_all([[card], [card]], detail_result=detail)
        with p1, p2, p3, p4:
            result = Ia44AmapList().call()
        assert result[0]["contact"] == {"name": "", "emails": ["contact@test.example"], "phones": []}
        assert result[0]["website"] == "https://test.example"

    def test_products_from_detail(self) -> None:
        card = _card("amap-01")
        detail = {**_EMPTY_DETAIL, 'products': ['Légumes', 'Fruits']}
        p1, p2, p3, p4 = _patch_all([[card], [card]], detail_result=detail)
        with p1, p2, p3, p4:
            result = Ia44AmapList().call()
        assert result[0]["products"] == [
            {"name": "Légumes", "category": ""},
            {"name": "Fruits", "category": ""},
        ]

    def test_farms_empty_when_no_farmer_list_url(self) -> None:
        card = _card("amap-01")
        p1, p2, p3, p4 = _patch_all([[card], [card]])
        with p1, p2, p3, p4:
            result = Ia44AmapList().call()
        assert result[0]["farms"] == []

    def test_farms_fetched_when_farmer_list_url_present(self) -> None:
        card = _card("amap-01")
        farm_card = _card("farm-01", name="Ferme A")
        detail = {**_EMPTY_DETAIL, 'farmer_list_url': 'https://www.amap44.org/?location=100'}
        farm_detail = {
            'name': 'Ferme A', 'city': 'NANTES', 'emails': ['a@test.example'], 'website': '',
            'protocols': {'ab_certification': True},
        }
        # list parser calls: page1, page2 (stop), farmer list page
        p1, p2, p3, p4 = _patch_all(
            [[card], [card], [farm_card]],
            detail_result=detail,
            farm_detail_result=farm_detail,
        )
        with p1, p2, p3, p4:
            result = Ia44AmapList().call()
        assert len(result[0]["farms"]) == 1
        assert result[0]["farms"][0]["id"] == "farm-01"
        assert result[0]["farms"][0]["contact"]["emails"] == ["a@test.example"]
        assert result[0]["farms"][0]["protocols"] == {'ab_certification': True}

    def test_amap_cards_filtered_from_farmer_list(self) -> None:
        card = _card("amap-01")
        amap_in_list = _card("amap-mixte", has_amap_cat=True)
        farmer_card = _card("farm-01", name="Ferme A")
        detail = {**_EMPTY_DETAIL, 'farmer_list_url': 'https://www.amap44.org/?location=100'}
        p1, p2, p3, p4 = _patch_all(
            [[card], [card], [amap_in_list, farmer_card]],
            detail_result=detail,
        )
        with p1, p2, p3, p4:
            result = Ia44AmapList().call()
        assert len(result[0]["farms"]) == 1
        assert result[0]["farms"][0]["id"] == "farm-01"

    def test_raises_on_http_error(self) -> None:
        with patch("amap_collector.core.ia44.endpoint.requests.get") as mock_get, \
             patch("amap_collector.core.ia44.endpoint.Ia44AmapListParser"), \
             patch("amap_collector.core.ia44.endpoint.Ia44AmapDetailParser"), \
             patch("amap_collector.core.ia44.endpoint.Ia44FarmerDetailParser"):
            mock_get.return_value.raise_for_status.side_effect = requests.HTTPError()
            with pytest.raises(requests.HTTPError):
                Ia44AmapList().call()


def _farm_card(slug: str, name: str = "Ferme Test") -> dict:
    return {
        'slug': slug,
        'name': name,
        'abstract': None,
        'address': '5 route des Champs, 44000 NANTES',
        'website': '',
        'category_hrefs': ['?ait-items=producteur'],
    }


_EMPTY_FARM_DETAIL: dict = {
    'name': '', 'address': '', 'city': '', 'emails': [], 'website': '', 'protocols': {},
}


def _patch_farm_list(list_side_effects, farm_detail_result=None):
    list_mock = MagicMock()
    list_mock.parse.side_effect = list_side_effects

    detail_mock = MagicMock()
    detail_mock.parse.return_value = farm_detail_result or _EMPTY_FARM_DETAIL.copy()

    return (
        patch("amap_collector.core.ia44.endpoint.requests.get"),
        patch("amap_collector.core.ia44.endpoint.Ia44AmapListParser", return_value=list_mock),
        patch("amap_collector.core.ia44.endpoint.Ia44FarmerDetailParser", return_value=detail_mock),
    )


class TestIa44FarmList:
    def test_returns_empty_when_first_page_is_empty(self) -> None:
        p1, p2, p3 = _patch_farm_list([[]])
        with p1, p2, p3:
            result = Ia44FarmList().call()
        assert result == []

    def test_pagination_stops_when_all_slugs_seen(self) -> None:
        card = _farm_card("farm-01")
        p1, p2, p3 = _patch_farm_list([[card], [card]])
        with p1, p2 as MockList, p3:
            result = Ia44FarmList().call()
        assert MockList.return_value.parse.call_count == 2
        assert len(result) == 1

    def test_slug_becomes_id(self) -> None:
        card = _farm_card("farm-01")
        p1, p2, p3 = _patch_farm_list([[card], [card]])
        with p1, p2, p3:
            result = Ia44FarmList().call()
        assert result[0]["id"] == "farm-01"
        assert "slug" not in result[0]

    def test_detail_enriches_result(self) -> None:
        card = _farm_card("farm-01", name="Ferme A")
        detail = {**_EMPTY_FARM_DETAIL, 'city': 'NANTES', 'emails': ['f@test.example'], 'website': 'https://ferme.example'}
        p1, p2, p3 = _patch_farm_list([[card], [card]], farm_detail_result=detail)
        with p1, p2, p3:
            result = Ia44FarmList().call()
        assert result[0]["city"] == "NANTES"
        assert result[0]["contact"]["emails"] == ["f@test.example"]
        assert result[0]["website"] == "https://ferme.example"

    def test_protocols_from_detail(self) -> None:
        card = _farm_card("farm-01")
        detail = {**_EMPTY_FARM_DETAIL, 'protocols': {'ab_certification': True}}
        p1, p2, p3 = _patch_farm_list([[card], [card]], farm_detail_result=detail)
        with p1, p2, p3:
            result = Ia44FarmList().call()
        assert result[0]["protocols"] == {'ab_certification': True}

    def test_raises_on_http_error(self) -> None:
        with patch("amap_collector.core.ia44.endpoint.requests.get") as mock_get, \
             patch("amap_collector.core.ia44.endpoint.Ia44AmapListParser"), \
             patch("amap_collector.core.ia44.endpoint.Ia44FarmerDetailParser"):
            mock_get.return_value.raise_for_status.side_effect = requests.HTTPError()
            with pytest.raises(requests.HTTPError):
                Ia44FarmList().call()
