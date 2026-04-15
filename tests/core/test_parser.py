from pathlib import Path
import pytest
from amap_scraper.core.parser import AmapListParser

FIXTURE = (Path(__file__).parent.parent / "fixtures" / "amap_list.html").read_text(encoding="utf-8")


@pytest.fixture
def parser() -> AmapListParser:
    return AmapListParser()


@pytest.fixture
def results(parser: AmapListParser) -> list:
    return parser.parse(FIXTURE)


def test_empty_html_returns_empty_list(parser: AmapListParser) -> None:
    assert parser.parse("<html></html>") == []


def test_parse_returns_correct_count(results: list) -> None:
    # 3 articles: first has 1 partage, second has 1, third has 2 → 4 entries total
    assert len(results) == 4


def test_completed_status(results: list) -> None:
    amap = results[0]
    assert amap["status"] == "completed"


def test_available_status(results: list) -> None:
    amap = results[1]
    assert amap["status"] == "available_places"


def test_name_extracted(results: list) -> None:
    assert results[0]["name"] == "AMAP Les Mauvaises Herbes"


def test_website_extracted(results: list) -> None:
    assert results[0]["website"] == "http://lesmauvaisesherbes.fr"


def test_missing_website_is_empty_string(results: list) -> None:
    assert results[1]["website"] == ""


def test_address_space_between_street_and_zip(results: list) -> None:
    assert results[1]["place"]["address"] == "6 rue Fernand Laguide, 91100 CORBEIL-ESSONNES"


def test_address_paris(results: list) -> None:
    assert results[0]["place"]["address"] == "2 bis rue de l'Ourcq, 75019 PARIS"


def test_place_name(results: list) -> None:
    assert results[0]["place"]["name"] == "La Ferme du Rail"


def test_delivery_time_stripped_of_label(results: list) -> None:
    assert results[0]["place"]["delivery_time"] == "Samedi 11h30-12h30"


def test_contact_name_stripped_of_label(results: list) -> None:
    assert results[0]["contact"]["name"] == "Le bureau de l'AMAP"


def test_contact_email_extracted(results: list) -> None:
    assert results[0]["contact"]["emails"] == ["bureau@amap19.fr"]


def test_contact_phone_extracted(results: list) -> None:
    assert results[1]["contact"]["phones"] == ["06 12 34 56 78"]


def test_missing_phone_is_empty_list(results: list) -> None:
    assert results[0]["contact"]["phones"] == []


def test_multiple_emails_extracted(results: list) -> None:
    # Third article, first partage (index 2) has two emails
    assert results[2]["contact"]["emails"] == ["jean@martin.fr", "contact@multisite.fr"]


def test_comment_extracted(results: list) -> None:
    assert results[0]["comment"] == "legumes oeufs volailles miel pain"


def test_multiple_partages_produce_multiple_entries(results: list) -> None:
    # Entries at index 2 and 3 both belong to AMAP Multi-Site
    assert results[2]["name"] == "AMAP Multi-Site"
    assert results[3]["name"] == "AMAP Multi-Site"
    assert results[2]["place"]["name"] == "Site A"
    assert results[3]["place"]["name"] == "Site B"


def test_deduplication_removes_identical_entries(parser: AmapListParser) -> None:
    # Parsing the same HTML twice must yield the same count (no duplicates added)
    first = parser.parse(FIXTURE)
    second = parser.parse(FIXTURE)
    assert len(first) == len(second) == 4
