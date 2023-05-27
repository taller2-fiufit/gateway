import asyncio
from typing import Any, Dict
from fastapi import FastAPI
from httpx import AsyncClient, RequestError

from src.api.model.service import Service
from src.db.session import SessionLocal
from src.db import services as services_db
from src.logging import warn


async def retrieve_schema(service: Service) -> Dict[str, Any]:
    try:
        async with AsyncClient(
            base_url=service.url or ""
        ) as client:  # never None
            response = await client.get("/openapi.json")

        response = response.json()
        return response if isinstance(response, Dict) else {}
    except RequestError as e:
        warn(f"Failed to retrieve schema: {e}")

    return {}


def nested_update(
    app_schema: Dict[str, Any], child_schema: Dict[str, Any]
) -> Dict[str, Any]:
    for k, v in child_schema.items():
        if k in app_schema and isinstance(v, Dict):
            nested_update(app_schema[k], v)
        else:
            app_schema[k] = v

    return app_schema


async def update_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    async with SessionLocal() as session:
        services = await services_db.get_all_services(
            session, blocked=False, with_statuses=False
        )

    children_schemas = await asyncio.gather(
        *[retrieve_schema(svc) for svc in services]
    )

    for child_schema in children_schemas:
        schema = nested_update(schema, child_schema)

    return schema


async def regenerate_openapi(app: FastAPI) -> None:
    try:
        initial_schema = app.openapi().copy()
        while True:
            schema = await update_schema(initial_schema.copy())
            app.openapi_schema = schema
            await asyncio.sleep(8)
    except asyncio.CancelledError:  # task was cancelled
        return


def launch_openapi_generator(app: FastAPI) -> asyncio.Task[Any]:
    return asyncio.create_task(regenerate_openapi(app))
