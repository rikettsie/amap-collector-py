import pytest
from amap_collector.core.whole.validations import ALLOWED_DEPTS, validate_department, WholeValidationError
from amap_collector.core.idf.validations import ALLOWED_DEPTS as IDF_DEPTS
from amap_collector.core.hn.validations import ALLOWED_DEPTS as HN_DEPTS
from amap_collector.core.ia44.validations import ALLOWED_DEPTS as IA44_DEPTS


def test_idf_depts_excluded() -> None:
    for dept in IDF_DEPTS:
        assert dept not in ALLOWED_DEPTS


def test_hn_depts_excluded() -> None:
    for dept in HN_DEPTS:
        assert dept not in ALLOWED_DEPTS


def test_ia44_depts_excluded() -> None:
    for dept in IA44_DEPTS:
        assert dept not in ALLOWED_DEPTS


def test_common_dept_is_allowed() -> None:
    assert "18" in ALLOWED_DEPTS


def test_dept_01_is_allowed() -> None:
    assert "01" in ALLOWED_DEPTS


def test_validate_accepts_valid_dept() -> None:
    assert validate_department("18") == "18"


def test_validate_coerces_int() -> None:
    assert validate_department(18) == "18"


def test_validate_raises_for_idf_dept() -> None:
    with pytest.raises(WholeValidationError):
        validate_department("75")


def test_validate_raises_for_unknown_code() -> None:
    with pytest.raises(WholeValidationError):
        validate_department("99")
