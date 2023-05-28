import asyncio
from typing import List
from cachetools import TTLCache
from httpx import AsyncClient, RequestError

from src.api.model.service import Service
from src.logging import warn


async def _updated_service_status(service: Service) -> bool:
    try:
        assert service.url is not None  # cannot fail
        async with AsyncClient(base_url=service.url) as client:
            response = await client.get("/health")
        return response.is_success
    except RequestError as e:
        warn(f"Failed to retrieve status from '{service.name}': {e}")

    return False


status_cache: TTLCache[Service, bool] = TTLCache(maxsize=1024, ttl=4)


async def updated_service_status(service: Service) -> bool:
    if service not in status_cache:
        status_cache[service] = await _updated_service_status(service)

    return status_cache[service]


async def update_statuses(services: List[Service]) -> None:
    statuses = await asyncio.gather(
        *[updated_service_status(svc) for svc in services]
    )

    for status, service in zip(statuses, services):
        service.up = status
