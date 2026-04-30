from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from amap_collector.cli.params import app
from amap_collector.core.router import AmapClientBuilderError

runner = CliRunner()


def _mock_builder(
    MockBuilder,
    dept: str = "75",
    zip_code: str | None = None,
    supports_farm_list: bool = False,
    supports_km_radius: bool = False,
    supports_zip_code: bool = False,
) -> MagicMock:
    instance = MockBuilder.return_value
    instance.supports_farm_list.return_value = supports_farm_list
    instance.supports_km_radius.return_value = supports_km_radius
    instance.supports_zip_code.return_value = supports_zip_code
    instance.target.return_value = {"dept": dept, "zip_code": zip_code}
    client = MagicMock()
    client.with_department.return_value = client
    client.with_km_radius.return_value = client
    client.with_zip_code.return_value = client
    client.get_amap_list.return_value = []
    client.get_farm_list.return_value = []
    instance.get_client.return_value = client
    return client


class TestOutputFileValidation:
    def test_invalid_extension_exits_with_error(self) -> None:
        result = runner.invoke(app, ["75", "--output-file", "out.txt"])
        assert result.exit_code == 1
        assert "json or .csv" in result.output

    def test_valid_json_extension_accepted(self, tmp_path) -> None:
        out = tmp_path / "result.json"
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            _mock_builder(MockBuilder)
            result = runner.invoke(app, ["75", "--output-file", str(out)])
        assert result.exit_code == 0

    def test_valid_csv_extension_accepted(self, tmp_path) -> None:
        out = tmp_path / "result.csv"
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            _mock_builder(MockBuilder)
            result = runner.invoke(app, ["75", "--output-file", str(out)])
        assert result.exit_code == 0


class TestParameterForwarding:
    def test_department_forwarded(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            client = _mock_builder(MockBuilder, dept="92")
            runner.invoke(app, ["92"])
        client.with_department.assert_called_once_with("92")

    def test_km_radius_forwarded_when_supported(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            client = _mock_builder(MockBuilder, supports_km_radius=True)
            runner.invoke(app, ["75", "--km-radius", "10"])
        client.with_km_radius.assert_called_once_with("10")

    def test_km_radius_not_supported_exits_with_1(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            _mock_builder(MockBuilder, supports_km_radius=False)
            result = runner.invoke(app, ["76", "--km-radius", "10"])
        assert result.exit_code == 1
        assert "not supported" in result.output

    def test_zip_code_forwarded_when_supported(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            client = _mock_builder(MockBuilder, zip_code="75019", supports_zip_code=True)
            runner.invoke(app, ["75019"])
        client.with_zip_code.assert_called_once_with("75019")

    def test_zip_code_not_supported_exits_with_1(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            _mock_builder(MockBuilder, zip_code="76000", supports_zip_code=False)
            result = runner.invoke(app, ["76000"])
        assert result.exit_code == 1
        assert "not supported" in result.output

    def test_no_zip_code_not_forwarded(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            client = _mock_builder(MockBuilder)
            runner.invoke(app, ["75"])
        client.with_zip_code.assert_not_called()


class TestFarmsOnly:
    def test_farms_only_calls_get_farm_list(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            client = _mock_builder(MockBuilder, dept="76", supports_farm_list=True)
            runner.invoke(app, ["76", "--farms-only"])
        client.get_farm_list.assert_called_once()
        client.get_amap_list.assert_not_called()

    def test_farms_only_not_supported_exits_with_1(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            _mock_builder(MockBuilder, supports_farm_list=False)
            result = runner.invoke(app, ["75", "--farms-only"])
        assert result.exit_code == 1
        assert "not supported" in result.output

    def test_without_farms_only_calls_get_amap_list(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            client = _mock_builder(MockBuilder)
            runner.invoke(app, ["75"])
        client.get_amap_list.assert_called_once()
        client.get_farm_list.assert_not_called()


class TestErrorHandling:
    def test_invalid_department_exits_with_1(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            MockBuilder.side_effect = AmapClientBuilderError("invalid dept")
            result = runner.invoke(app, ["02"])
        assert result.exit_code == 1

    def test_client_error_exits_with_1(self) -> None:
        with patch("amap_collector.cli.params.AmapClientBuilder") as MockBuilder:
            client = _mock_builder(MockBuilder)
            client.get_amap_list.side_effect = RuntimeError("network error")
            result = runner.invoke(app, ["75"])
        assert result.exit_code == 1
