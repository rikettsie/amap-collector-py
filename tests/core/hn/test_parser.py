from pathlib import Path
import pytest
from amap_collector.core.hn.parser import HnAmapListParser, HnAmapDetailParser, HnFarmDetailParser, HnFarmListParser

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "hn"


def load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def list_parser() -> HnAmapListParser:
    return HnAmapListParser()


@pytest.fixture
def results(list_parser: HnAmapListParser) -> list:
    return list_parser.parse(load("amap_list.html"))


@pytest.fixture
def detail_parser() -> HnAmapDetailParser:
    return HnAmapDetailParser()


@pytest.fixture
def detail(detail_parser: HnAmapDetailParser) -> dict:
    return detail_parser.parse(load("amap_detail.html"))


class TestHnAmapListParserEdgeCases:
    def test_no_scripts_returns_empty(self, list_parser: HnAmapListParser) -> None:
        assert list_parser.parse(load("empty.html")) == []

    def test_no_amaps_key_returns_empty(self, list_parser: HnAmapListParser) -> None:
        assert list_parser.parse(load("no_amaps.html")) == []


class TestHnAmapListParserResults:
    def test_parse_returns_correct_count(self, results: list) -> None:
        assert len(results) == 2

    def test_id_extracted(self, results: list) -> None:
        assert results[0]["id"] == "amap-1"

    def test_slug_included(self, results: list) -> None:
        assert results[0]["slug"] == "amap-de-rouen"

    def test_name_extracted(self, results: list) -> None:
        assert results[0]["name"] == "AMAP de Rouen"

    def test_abstract_extracted(self, results: list) -> None:
        assert results[0]["abstract"] == "Des légumes frais"

    def test_abstract_none_when_missing(self, results: list) -> None:
        assert results[1]["abstract"] is None

    def test_status_is_none(self, results: list) -> None:
        assert results[0]["status"] is None

    def test_comment_is_none(self, results: list) -> None:
        assert results[0]["comment"] is None

    def test_delivery_address_formatted(self, results: list) -> None:
        assert results[0]["delivery"]["address"] == "12 rue de la Paix 76000 ROUEN"

    def test_delivery_place_name_is_none(self, results: list) -> None:
        assert results[0]["delivery"]["place_name"] is None

    def test_delivery_days_parsed(self, results: list) -> None:
        assert results[0]["delivery"]["days"] == [
            {"weekDay": "Samedi", "openHour": "10:00:00.000", "closeHour": "11:00:00.000"}
        ]

    def test_empty_delivery_days(self, results: list) -> None:
        assert results[1]["delivery"]["days"] == []

    def test_delivery_basket_count(self, results: list) -> None:
        assert results[0]["delivery"]["basket_count"] == 20

    def test_contact_address_formatted(self, results: list) -> None:
        assert results[0]["contact_address"] == "5 av Victor Hugo 76000 ROUEN"

    def test_products_parsed(self, results: list) -> None:
        assert results[0]["products"] == [{"name": "Légumes", "category": "Maraîchage"}]

    def test_empty_products(self, results: list) -> None:
        assert results[1]["products"] == []

    def test_farms_parsed(self, results: list) -> None:
        assert results[0]["farms"] == [
            {"id": "farm-1", "slug": "ferme-du-soleil", "name": "Ferme du Soleil", "city": "Rouen"}
        ]

    def test_empty_farms(self, results: list) -> None:
        assert results[1]["farms"] == []


class TestHnAmapDetailParser:
    def test_no_contact_block_returns_empty(self, detail_parser: HnAmapDetailParser) -> None:
        assert detail_parser.parse(load("no_contact.html")) == {}

    def test_name_extracted(self, detail: dict) -> None:
        assert detail["name"] == "Jean Dupont"

    def test_email_extracted(self, detail: dict) -> None:
        assert detail["emails"] == ["jean@example.com"]

    def test_phone_extracted(self, detail: dict) -> None:
        assert detail["phones"] == ["06 12 34 56 78"]

    def test_website_extracted(self, detail: dict) -> None:
        assert detail["website"] == "https://www.amap-rouen.fr"


class TestHnFarmDetailParser:
    def test_parses_farm_contact(self) -> None:
        parser = HnFarmDetailParser()
        result = parser.parse(load("farm_detail.html"))
        assert result["name"] == "Marie Hey"
        assert result["emails"] == ["marie@ferme-bio.paris"]
        assert result["phones"] == ["06 11 11 11 01"]
        assert result["website"] == "https://www.ferme-bio.paris"

    def test_no_contact_returns_empty(self) -> None:
        parser = HnFarmDetailParser()
        assert parser.parse(load("no_contact.html")) == {}


class TestHnFarmListParser:
    def test_no_scripts_returns_empty(self) -> None:
        assert HnFarmListParser().parse(load("empty.html")) == []

    def test_no_farms_key_returns_empty(self) -> None:
        assert HnFarmListParser().parse(load("no_amaps.html")) == []

    def test_amap_list_page_not_mistaken_for_farm_list(self) -> None:
        assert HnFarmListParser().parse(load("amap_list.html")) == []

    def test_parse_returns_correct_count(self) -> None:
        result = HnFarmListParser().parse(load("farm_list.html"))
        assert len(result) == 2

    def test_id_extracted(self) -> None:
        result = HnFarmListParser().parse(load("farm_list.html"))
        assert result[0]["id"] == "farm-1"

    def test_slug_extracted(self) -> None:
        result = HnFarmListParser().parse(load("farm_list.html"))
        assert result[0]["slug"] == "ferme-test-1"

    def test_name_extracted(self) -> None:
        result = HnFarmListParser().parse(load("farm_list.html"))
        assert result[0]["name"] == "Ferme Test 1"

    def test_city_extracted(self) -> None:
        result = HnFarmListParser().parse(load("farm_list.html"))
        assert result[0]["city"] == "Rouen"
