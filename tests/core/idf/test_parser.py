from pathlib import Path
import pytest
from amap_collector.core.idf.parser import IdfAmapListParser, ParserError

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "idf"


def load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def parser() -> IdfAmapListParser:
    return IdfAmapListParser()


@pytest.fixture
def results(parser: IdfAmapListParser) -> list:
    return parser.parse(load("amap_list.html"))


def test_empty_html_returns_empty_list(parser: IdfAmapListParser) -> None:
    assert parser.parse(load("empty.html")) == []


def test_missing_container_in_full_page_raises(parser: IdfAmapListParser) -> None:
    with pytest.raises(ParserError, match="liste-fiches"):
        parser.parse(load("no_container.html"))


def test_missing_amap_nom_raises(parser: IdfAmapListParser) -> None:
    with pytest.raises(ParserError, match="amap-nom"):
        parser.parse(load("missing_amap_nom.html"))


def test_missing_partage_nom_returns_none(parser: IdfAmapListParser) -> None:
    results = parser.parse(load("missing_partage_nom.html"))
    assert results[0]["delivery"]["place_name"] is None


def test_missing_partage_adresse_returns_empty_string(parser: IdfAmapListParser) -> None:
    results = parser.parse(load("missing_partage_adresse.html"))
    assert results[0]["delivery"]["address"] == ""


def test_parse_returns_correct_count(results: list) -> None:
    # 3 articles: first has 1 partage, second has 1, third has 2 → 4 entries total
    assert len(results) == 4


def test_completed_status(results: list) -> None:
    assert results[0]["status"] == "completed"


def test_available_status(results: list) -> None:
    assert results[1]["status"] == "available_places"


def test_name_extracted(results: list) -> None:
    assert results[0]["name"] == "AMAP Les Mauvaises Herbes"


def test_website_extracted(results: list) -> None:
    assert results[0]["website"] == "http://lesmauvaisesherbes.fr"


def test_missing_website_is_empty_string(results: list) -> None:
    assert results[1]["website"] == ""


def test_address_space_between_street_and_zip(results: list) -> None:
    assert results[1]["delivery"]["address"] == "6 rue Fernand Laguide, 91100 CORBEIL-ESSONNES"


def test_address_paris(results: list) -> None:
    assert results[0]["delivery"]["address"] == "2 bis rue de l'Ourcq, 75019 PARIS"


def test_place_name(results: list) -> None:
    assert results[0]["delivery"]["place_name"] == "La Ferme du Rail"


def test_delivery_days_parsed(results: list) -> None:
    assert results[0]["delivery"]["days"] == [
        {"week_day": "Samedi", "open_hour": "11:30:00.000", "close_hour": "12:30:00.000"}
    ]


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
    assert results[2]["delivery"]["place_name"] == "Site A"
    assert results[3]["delivery"]["place_name"] == "Site B"


def test_deduplication_removes_identical_entries(parser: IdfAmapListParser) -> None:
    # Parsing the same HTML twice must yield the same count (no duplicates added)
    first = parser.parse(load("amap_list.html"))
    second = parser.parse(load("amap_list.html"))
    assert len(first) == len(second) == 4
