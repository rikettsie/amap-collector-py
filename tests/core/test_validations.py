from unittest.mock import patch
import pytest
from amap_collector.core.validations import (
    validate_department,
    validate_km_radius,
    validate_zip_code,
    ValidationError,
    ALLOWED_DEPTS,
    ALLOWED_RADII,
)


class TestValidateDepartment:
    def test_valid_departments(self) -> None:
        for dept in ALLOWED_DEPTS:
            assert validate_department(dept) == dept

    def test_accepts_int(self) -> None:
        assert validate_department(75) == "75"

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_department("99")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_department("")


class TestValidateKmRadius:
    def test_valid_radii(self) -> None:
        for r in ALLOWED_RADII:
            assert validate_km_radius(r) == r

    def test_accepts_int(self) -> None:
        assert validate_km_radius(5) == "5"

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_km_radius("3")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_km_radius("")



class TestValidateZipCode:
    def test_valid_zip_code(self) -> None:
        mock_response = {"code": "75019"}
        with patch("amap_collector.core.validations.ZipCodeInfo") as MockZip:
            MockZip.return_value.call.return_value = mock_response
            result = validate_zip_code("75019")
        assert result == "75019"

    def test_invalid_zip_returns_no_code(self) -> None:
        with patch("amap_collector.core.validations.ZipCodeInfo") as MockZip:
            MockZip.return_value.call.return_value = {}
            with pytest.raises(ValidationError):
                validate_zip_code("00000")

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(ValidationError):
            validate_zip_code("abcde")
