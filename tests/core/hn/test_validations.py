import pytest
from amap_collector.core.hn.validations import (
    validate_department,
    HnValidationError as ValidationError,
    ALLOWED_DEPTS,
)


class TestValidateDepartment:
    def test_valid_departments(self) -> None:
        for dept in ALLOWED_DEPTS:
            assert validate_department(dept) == dept

    def test_accepts_int(self) -> None:
        assert validate_department(27) == "27"

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_department("75")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_department("")
