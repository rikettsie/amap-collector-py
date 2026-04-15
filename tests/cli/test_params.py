from unittest.mock import patch
from typer.testing import CliRunner
from amap_scraper.cli.params import app

runner = CliRunner()


class TestOutputFileValidation:
    def test_invalid_extension_exits_with_error(self) -> None:
        result = runner.invoke(app, ["--output-file", "out.txt"])
        assert result.exit_code == 1
        assert "json or .csv" in result.output

    def test_valid_json_extension_accepted(self, tmp_path) -> None:
        out = tmp_path / "result.json"
        with patch("amap_scraper.cli.params.AmapClient") as MockClient:
            MockClient.return_value.with_department.return_value = MockClient.return_value
            MockClient.return_value.with_km_radius.return_value = MockClient.return_value
            MockClient.return_value.get_amap_list.return_value = []
            result = runner.invoke(app, ["--output-file", str(out)])
        assert result.exit_code == 0

    def test_valid_csv_extension_accepted(self, tmp_path) -> None:
        out = tmp_path / "result.csv"
        with patch("amap_scraper.cli.params.AmapClient") as MockClient:
            MockClient.return_value.with_department.return_value = MockClient.return_value
            MockClient.return_value.with_km_radius.return_value = MockClient.return_value
            MockClient.return_value.get_amap_list.return_value = []
            result = runner.invoke(app, ["--output-file", str(out)])
        assert result.exit_code == 0


class TestParameterForwarding:
    def _mock_client(self, MockClient):
        instance = MockClient.return_value
        instance.with_department.return_value = instance
        instance.with_km_radius.return_value = instance
        instance.with_zip_code.return_value = instance
        instance.get_amap_list.return_value = []
        return instance

    def test_department_forwarded(self) -> None:
        with patch("amap_scraper.cli.params.AmapClient") as MockClient:
            instance = self._mock_client(MockClient)
            runner.invoke(app, ["--department", "92"])
        instance.with_department.assert_called_once_with("92")

    def test_km_radius_forwarded(self) -> None:
        with patch("amap_scraper.cli.params.AmapClient") as MockClient:
            instance = self._mock_client(MockClient)
            runner.invoke(app, ["--km-radius", "10"])
        instance.with_km_radius.assert_called_once_with("10")

    def test_zip_code_forwarded(self) -> None:
        with patch("amap_scraper.cli.params.AmapClient") as MockClient:
            instance = self._mock_client(MockClient)
            runner.invoke(app, ["--zip-code", "75019"])
        instance.with_zip_code.assert_called_once_with("75019")


    def test_no_zip_code_not_forwarded(self) -> None:
        with patch("amap_scraper.cli.params.AmapClient") as MockClient:
            instance = self._mock_client(MockClient)
            runner.invoke(app, [])
        instance.with_zip_code.assert_not_called()


class TestErrorHandling:
    def test_validation_error_exits_with_1(self) -> None:
        with patch("amap_scraper.cli.params.AmapClient") as MockClient:
            from amap_scraper.core.validations import ValidationError
            MockClient.return_value.with_department.side_effect = ValidationError("bad dept")
            result = runner.invoke(app, ["--department", "99"])
        assert result.exit_code == 1

    def test_client_error_exits_with_1(self) -> None:
        with patch("amap_scraper.cli.params.AmapClient") as MockClient:
            from amap_scraper.core.client import AmapClientError
            instance = MockClient.return_value
            instance.with_department.return_value = instance
            instance.with_km_radius.return_value = instance
            instance.get_amap_list.side_effect = AmapClientError("network error")
            result = runner.invoke(app, [])
        assert result.exit_code == 1
