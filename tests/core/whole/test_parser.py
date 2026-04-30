from pathlib import Path
import pytest
from amap_collector.core.whole.parser import WholeIndexParser, WholeAmapListParser

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "whole"


def load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class TestWholeIndexParser:
    @pytest.fixture
    def parser(self) -> WholeIndexParser:
        return WholeIndexParser()

    def test_returns_none_for_empty_html(self, parser: WholeIndexParser) -> None:
        assert parser.find_dept_url(load("empty.html"), "18") is None

    def test_finds_dept_url(self, parser: WholeIndexParser) -> None:
        assert parser.find_dept_url(load("index_page.html"), "18") == "amap,cher,18.html"

    def test_returns_none_for_missing_dept(self, parser: WholeIndexParser) -> None:
        assert parser.find_dept_url(load("index_page.html"), "99") is None

    def test_finds_single_digit_dept_with_padded_code(self, parser: WholeIndexParser) -> None:
        assert parser.find_dept_url(load("index_page.html"), "01") == "amap,ain,01.html"

    def test_no_map_element_returns_none(self, parser: WholeIndexParser) -> None:
        html = "<html><body><p>No map here</p></body></html>"
        assert parser.find_dept_url(html, "18") is None


class TestWholeAmapListParser:
    @pytest.fixture
    def parser(self) -> WholeAmapListParser:
        return WholeAmapListParser()

    @pytest.fixture
    def results(self, parser: WholeAmapListParser) -> list:
        return parser.parse(load("dept_page.html"))

    def test_empty_html_returns_empty_list(self, parser: WholeAmapListParser) -> None:
        assert parser.parse(load("empty.html")) == []

    def test_parse_returns_correct_count(self, results: list) -> None:
        assert len(results) == 2

    def test_both_fdg1_and_fdg2_parsed(self, results: list) -> None:
        # Fixture has one FDG1 and one FDG2 card
        names = {r["name"] for r in results}
        assert "AMAP DES MARAIS" in names
        assert "AMAP des Bouchures" in names

    def test_id_extracted_from_fiche_amap_link(self, results: list) -> None:
        assert results[0]["id"] == "1914"

    def test_id_from_second_card(self, results: list) -> None:
        assert results[1]["id"] == "473"

    def test_name_with_link_strips_city(self, results: list) -> None:
        assert results[0]["name"] == "AMAP DES MARAIS"

    def test_name_without_link_strips_city(self, results: list) -> None:
        # Second card has no <a> inside <strong>
        assert results[1]["name"] == "AMAP des Bouchures"

    def test_email_from_mailto_href(self, results: list) -> None:
        assert results[0]["emails"] == ["contact@amap-bourges.fr"]

    def test_second_card_email(self, results: list) -> None:
        assert results[1]["emails"] == ["amapdesbouchures@outlook.fr"]

    def test_site_internet_href_extracted(self, results: list) -> None:
        assert results[0]["raw_websites"] == ["go.php?typ=1&id=1914"]

    def test_facebook_only_card_has_no_raw_website(self, results: list) -> None:
        # Second card has "Page facebook" link only, no "Site Internet"
        assert results[1]["raw_websites"] == []

    def test_products_parsed(self, results: list) -> None:
        assert results[0]["products"] == ["Légumes", "fromages", "oeufs"]

    def test_second_card_products(self, results: list) -> None:
        assert results[1]["products"] == ["Légumes", "oeufs", "volaille"]

    def test_distribution_extracted(self, results: list) -> None:
        assert "vendredi" in results[0]["distribution"]
        assert "17h30" in results[0]["distribution"]

    def test_distribution_excludes_phone_section(self, results: list) -> None:
        assert "Contact" not in results[1]["distribution"]
        assert "06 42 63 95 23" not in results[1]["distribution"]

    def test_phone_extracted_from_distribution_div(self, results: list) -> None:
        assert results[1]["phones"] == ["06 42 63 95 23"]

    def test_no_phone_returns_empty_list(self, results: list) -> None:
        assert results[0]["phones"] == []

    def test_card_without_name_skipped(self, parser: WholeAmapListParser) -> None:
        html = '<div class="col-md-6 TL PTB20b FDG1"><span>some text</span></div>'
        assert parser.parse(html) == []
