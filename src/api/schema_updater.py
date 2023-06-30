import asyncio
import copy
from typing import Any, Dict
from fastapi import FastAPI
from httpx import AsyncClient, RequestError

from src.db.model.service import DBService
from src.db.session import SessionLocal
from src.db import services as services_db
from src.logging import warn
from src.api.proxy import APIKEY_HEADER


async def retrieve_schema(service: DBService) -> Dict[str, Any]:
    headers = {APIKEY_HEADER: service.apikey}
    try:
        async with AsyncClient(
            base_url=service.url or ""
        ) as client:  # never None
            response = await client.get("/openapi.json", headers=headers)

        response = response.json()
        return response if isinstance(response, Dict) else {}
    except RequestError as e:
        warn(f"Failed to retrieve schema: {e}")

    return {}


def nested_update(
    app_schema: Dict[str, Any], child_schema: Dict[str, Any]
) -> Dict[str, Any]:
    for k, v in child_schema.items():
        if k not in app_schema:
            app_schema[k] = v
        elif isinstance(v, Dict):
            nested_update(app_schema[k], v)

    return app_schema


async def update_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    async with SessionLocal() as session:
        services = await services_db.get_all_services_inner(
            session, blocked=False
        )

    children_schemas = await asyncio.gather(
        *[retrieve_schema(svc) for svc in services]
    )

    for child_schema in children_schemas:
        schema = nested_update(schema, child_schema)

    return schema


async def regenerate_openapi(app: FastAPI) -> None:
    try:
        # save app's initial schema to use as base
        initial_schema = copy.deepcopy(app.openapi())
        while True:
            cloned = copy.deepcopy(initial_schema)
            schema = await update_schema(cloned)
            app.openapi_schema = schema
            await asyncio.sleep(8)
    except asyncio.CancelledError:  # task was cancelled
        return


def launch_openapi_generator(app: FastAPI) -> asyncio.Task[Any]:
    return asyncio.create_task(regenerate_openapi(app))
