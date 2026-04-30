from pathlib import Path
import pytest
from amap_collector.core.ia44.parser import Ia44AmapListParser, Ia44AmapDetailParser, Ia44FarmerDetailParser

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "ia44"


def load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def list_parser() -> Ia44AmapListParser:
    return Ia44AmapListParser()


@pytest.fixture
def results(list_parser: Ia44AmapListParser) -> list:
    return list_parser.parse(load("amap_list.html"))


@pytest.fixture
def detail_parser() -> Ia44AmapDetailParser:
    return Ia44AmapDetailParser()


@pytest.fixture
def detail(detail_parser: Ia44AmapDetailParser) -> dict:
    return detail_parser.parse(load("amap_detail.html"))


class TestIa44AmapListParserEdgeCases:
    def test_no_cards_returns_empty(self, list_parser: Ia44AmapListParser) -> None:
        assert list_parser.parse(load("empty.html")) == []


class TestIa44AmapListParserResults:
    def test_parse_returns_correct_count(self, results: list) -> None:
        assert len(results) == 2

    def test_slug_extracted(self, results: list) -> None:
        assert results[0]["slug"] == "amap-test-01"

    def test_name_extracted(self, results: list) -> None:
        assert results[0]["name"] == "AMAP Test Nantes"

    def test_abstract_extracted(self, results: list) -> None:
        assert results[0]["abstract"] == "Description bio locale."

    def test_abstract_none_when_missing(self, results: list) -> None:
        assert results[1]["abstract"] is None

    def test_address_extracted(self, results: list) -> None:
        assert results[0]["address"] == "1 rue des Tests, 44000 NANTES"

    def test_website_empty_when_missing(self, results: list) -> None:
        assert results[0]["website"] == ""

    def test_website_extracted(self, results: list) -> None:
        assert results[1]["website"] == "https://example.org"

    def test_category_hrefs_extracted(self, results: list) -> None:
        assert results[0]["category_hrefs"] == ["?ait-items=amap"]


class TestIa44AmapDetailParser:
    def test_no_fields_returns_empty_values(self, detail_parser: Ia44AmapDetailParser) -> None:
        result = detail_parser.parse(load("no_contact.html"))
        assert result["abstract"] is None
        assert result["address"] == ""
        assert result["days"] == []
        assert result["emails"] == []
        assert result["website"] == ""
        assert result["products"] == []
        assert result["farmer_list_url"] is None

    def test_abstract_extracted(self, detail: dict) -> None:
        assert detail["abstract"] == "Description complète de l'AMAP test."

    def test_address_extracted(self, detail: dict) -> None:
        assert detail["address"] == "1 rue des Tests, 44000 NANTES"

    def test_days_parsed_format_a(self, detail: dict) -> None:
        assert detail["days"] == [
            {"week_day": "Vendredi", "open_hour": "18:00:00.000", "close_hour": "19:30:00.000"}
        ]

    def test_email_extracted(self, detail: dict) -> None:
        assert detail["emails"] == ["contact@amap-test.example"]

    def test_website_extracted(self, detail: dict) -> None:
        assert detail["website"] == "https://www.amap-test.example"

    def test_products_extracted(self, detail: dict) -> None:
        assert detail["products"] == ["Légumes", "Fruits"]

    def test_farmer_list_url_extracted(self, detail: dict) -> None:
        assert detail["farmer_list_url"] == "https://www.amap44.org/?s=&category=&location=100&a=true"


class TestIa44FarmerDetailParser:
    def test_parses_farmer_detail(self) -> None:
        parser = Ia44FarmerDetailParser()
        result = parser.parse(load("farm_detail.html"))
        assert result["name"] == "Ferme Test Bio"
        assert result["address"] == "10 chemin des Champs, 44130 VILLE-TEST"
        assert result["city"] == "VILLE-TEST"
        assert result["emails"] == ["ferme@test.example"]
        assert result["website"] == "https://ferme-test.example"

    def test_protocols_extracted(self) -> None:
        parser = Ia44FarmerDetailParser()
        result = parser.parse(load("farm_detail.html"))
        assert result["protocols"] == {
            "ab_certification": True,
            "ab_conversion": False,
            "bio_coherence_certification": False,
            "demeter_certification": True,
            "no_pest_chemistry": True,
        }

    def test_no_fields_returns_empty_values(self) -> None:
        parser = Ia44FarmerDetailParser()
        result = parser.parse(load("no_contact.html"))
        assert result["name"] == ""
        assert result["city"] == ""
        assert result["emails"] == []
        assert result["website"] == ""
        assert result["protocols"] == {}


class TestIa44AmapListParserFarmerListPage:
    def test_parses_all_cards(self, list_parser: Ia44AmapListParser) -> None:
        cards = list_parser.parse(load("farmer_list.html"))
        assert len(cards) == 3

    def test_amap_card_has_amap_category_href(self, list_parser: Ia44AmapListParser) -> None:
        cards = list_parser.parse(load("farmer_list.html"))
        amap_card = next(c for c in cards if c["slug"] == "amap-mixte-01")
        assert any("ait-items=amap" in h for h in amap_card["category_hrefs"])

    def test_farmer_cards_lack_amap_category(self, list_parser: Ia44AmapListParser) -> None:
        cards = list_parser.parse(load("farmer_list.html"))
        farmer_cards = [c for c in cards if c["slug"] != "amap-mixte-01"]
        for card in farmer_cards:
            assert not any("ait-items=amap" in h for h in card["category_hrefs"])
