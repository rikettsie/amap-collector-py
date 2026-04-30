import asyncio
import logging
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from amap_collector.core.collector import collect, _collect_one, CollectionError, MAX_CONCURRENT

_PATCH = "amap_collector.core.collector.AmapClientBuilder"


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
    client.get_amap_list.return_value = [{"name": "AMAP"}]
    client.get_farm_list.return_value = [{"name": "Farm"}]
    instance.get_client.return_value = client
    return client


class TestCollectOne:
    def test_department_forwarded(self) -> None:
        with patch(_PATCH) as MockBuilder:
            client = _mock_builder(MockBuilder, dept="92")
            asyncio.run(_collect_one("92", None, False))
        client.with_department.assert_called_once_with("92")

    def test_calls_get_amap_list_by_default(self) -> None:
        with patch(_PATCH) as MockBuilder:
            client = _mock_builder(MockBuilder)
            asyncio.run(_collect_one("75", None, False))
        client.get_amap_list.assert_called_once()
        client.get_farm_list.assert_not_called()

    def test_farms_only_calls_get_farm_list(self) -> None:
        with patch(_PATCH) as MockBuilder:
            client = _mock_builder(MockBuilder, dept="76", supports_farm_list=True)
            asyncio.run(_collect_one("76", None, True))
        client.get_farm_list.assert_called_once()
        client.get_amap_list.assert_not_called()

    def test_farms_only_not_supported_raises(self) -> None:
        with patch(_PATCH) as MockBuilder:
            _mock_builder(MockBuilder, supports_farm_list=False)
            with pytest.raises(CollectionError, match="farms-only"):
                asyncio.run(_collect_one("75", None, True))

    def test_km_radius_forwarded_when_supported(self) -> None:
        with patch(_PATCH) as MockBuilder:
            client = _mock_builder(MockBuilder, supports_km_radius=True)
            asyncio.run(_collect_one("75", "10", False))
        client.with_km_radius.assert_called_once_with("10")

    def test_km_radius_not_supported_logs_warning_and_continues(self, caplog) -> None:
        with patch(_PATCH) as MockBuilder:
            client = _mock_builder(MockBuilder, supports_km_radius=False)
            with caplog.at_level(logging.WARNING, logger="amap_collector.core.collector"):
                asyncio.run(_collect_one("76", "10", False))
        assert "km-radius" in caplog.text
        client.with_km_radius.assert_not_called()
        client.get_amap_list.assert_called_once()

    def test_zip_code_forwarded_when_supported(self) -> None:
        with patch(_PATCH) as MockBuilder:
            client = _mock_builder(MockBuilder, zip_code="75019", supports_zip_code=True)
            asyncio.run(_collect_one("75019", None, False))
        client.with_zip_code.assert_called_once_with("75019")

    def test_zip_code_not_supported_raises(self) -> None:
        with patch(_PATCH) as MockBuilder:
            _mock_builder(MockBuilder, zip_code="76000", supports_zip_code=False)
            with pytest.raises(CollectionError, match="zip_code"):
                asyncio.run(_collect_one("76000", None, False))

    def test_no_zip_code_not_forwarded(self) -> None:
        with patch(_PATCH) as MockBuilder:
            client = _mock_builder(MockBuilder, zip_code=None)
            asyncio.run(_collect_one("75", None, False))
        client.with_zip_code.assert_not_called()


class TestCollect:
    def test_single_code_returns_results(self) -> None:
        with patch(_PATCH) as MockBuilder:
            client = _mock_builder(MockBuilder)
            results = asyncio.run(collect(["75"]))
        assert results == [{"name": "AMAP"}]
        client.get_amap_list.assert_called_once()

    def test_multi_code_merges_results(self) -> None:
        async def fake_one(ac, km_radius, farms_only):
            return [{"code": ac}]

        with patch("amap_collector.core.collector._collect_one", side_effect=fake_one):
            results = asyncio.run(collect(["75", "76"]))

        assert len(results) == 2
        assert {r["code"] for r in results} == {"75", "76"}

    def test_partial_failure_skips_failed_code(self, caplog) -> None:
        async def fake_one(ac, km_radius, farms_only):
            if ac == "76":
                raise RuntimeError("network error")
            return [{"code": ac}]

        with patch("amap_collector.core.collector._collect_one", side_effect=fake_one):
            with caplog.at_level(logging.WARNING, logger="amap_collector.core.collector"):
                results = asyncio.run(collect(["75", "76"]))

        assert results == [{"code": "75"}]
        assert "76" in caplog.text

    def test_all_fail_returns_empty(self) -> None:
        async def fake_one(ac, km_radius, farms_only):
            raise RuntimeError("error")

        with patch("amap_collector.core.collector._collect_one", side_effect=fake_one):
            results = asyncio.run(collect(["75", "76"]))

        assert results == []

    def test_max_concurrent_greater_than_codes_runs_all(self) -> None:
        async def fake_one(ac, km_radius, farms_only):
            return [{"code": ac}]

        with patch("amap_collector.core.collector._collect_one", side_effect=fake_one):
            results = asyncio.run(collect(["75", "76"], max_concurrent=100))

        assert {r["code"] for r in results} == {"75", "76"}

    def test_max_concurrent_limits_parallelism(self) -> None:
        running = 0
        peak = 0

        async def fake_one(ac, km_radius, farms_only):
            nonlocal running, peak
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0)
            running -= 1
            return [{"code": ac}]

        codes = ["75", "76", "91", "92", "93"]
        with patch("amap_collector.core.collector._collect_one", side_effect=fake_one):
            asyncio.run(collect(codes, max_concurrent=2))

        assert peak <= 2
