import asyncio
import logging
from typing import Any, Optional

from amap_collector.core.router import AmapClientBuilder, AmapClientBuilderError

logger = logging.getLogger(__name__)

MAX_CONCURRENT: int = 8


class CollectionError(ValueError):
    pass


async def collect(
    area_codes: list[str],
    km_radius: Optional[str] = None,
    farms_only: bool = False,
    max_concurrent: int = MAX_CONCURRENT,
) -> list[dict[str, Any]]:
    if len(area_codes) == 1:
        return await _collect_one(area_codes[0], km_radius, farms_only)

    sem = asyncio.Semaphore(min(max_concurrent, len(area_codes)))

    async def bounded(ac: str):
        async with sem:
            return await _collect_one(ac, km_radius, farms_only)

    results = await asyncio.gather(*[bounded(ac) for ac in area_codes], return_exceptions=True)

    merged: list[dict[str, Any]] = []
    for ac, result in zip(area_codes, results):
        if isinstance(result, BaseException):
            logger.warning("Skipping %s: %s", ac, result)
        else:
            merged.extend(result)
    return merged


async def _collect_one(
    area_code: str,
    km_radius: Optional[str],
    farms_only: bool,
) -> list[dict[str, Any]]:
    client_builder = AmapClientBuilder(area_code)
    target = client_builder.target()
    client = client_builder.get_client()

    if farms_only and not client_builder.supports_farm_list():
        raise CollectionError(f"--farms-only is not supported for region {area_code}")

    if km_radius:
        if client_builder.supports_km_radius():
            client.with_km_radius(km_radius)
        else:
            logger.warning("--km-radius is not supported for region %s, ignoring", area_code)

    if target["zip_code"]:
        if client_builder.supports_zip_code():
            client.with_zip_code(target["zip_code"])
        else:
            raise CollectionError(f"zip_code scraping is not supported for region {area_code}")

    client.with_department(target["dept"])
    return client.get_farm_list() if farms_only else client.get_amap_list()
