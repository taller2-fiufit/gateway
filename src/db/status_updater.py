import asyncio
from typing import List
from cachetools.func import ttl_cache
from httpx import AsyncClient, RequestError

from src.api.model.service import Service
from src.logging import warn


@ttl_cache(maxsize=32, ttl=4)
async def updated_service_status(service: Service) -> bool:
    try:
        async with AsyncClient(
            base_url=service.url or ""
        ) as client:  # never None
            response = await client.get("/health")
        return response.is_success
    except RequestError as e:
        warn(str(e))

    return False


async def update_statuses(services: List[Service]) -> None:
    statuses = await asyncio.gather(
        *[updated_service_status(svc) for svc in services]
    )

    for status, service in zip(statuses, services):
        service.up = status
