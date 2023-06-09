from http import HTTPStatus
from httpx import AsyncClient
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from src.api.model.service import AddService, ServiceWithApikey

from src.auth import get_admin, get_user, ignore_auth
from src.db.migration import downgrade_db
from src.main import lifespan, app
from src.test_utils import assert_returns_empty
from src.api.proxy import (
    get_routing_table,
    build_routing_table,
)


# https://stackoverflow.com/questions/71925980/cannot-perform-operation-another-operation-is-in-progress-in-pytest
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ---------------
# COMMON FIXTURES
# ---------------


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    # reset database
    await downgrade_db()

    # https://fastapi.tiangolo.com/advanced/testing-dependencies/
    # dummy authentication
    app.dependency_overrides[get_user] = ignore_auth
    app.dependency_overrides[get_admin] = ignore_auth
    # don't cache routing table
    app.dependency_overrides[get_routing_table] = build_routing_table

    async with lifespan(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client


# -----------------
# SERVICES FIXTURES
# -----------------


@pytest.fixture
async def check_empty_services(client: AsyncClient) -> None:
    await assert_returns_empty(client, "/services")
    response = await client.get("/services/count")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"count": 0}


@pytest.fixture
async def created_body(client: AsyncClient) -> ServiceWithApikey:
    body = AddService(
        name="test service", url="http://localhost", path="^/local.*"
    )

    response = await client.post("/services", json=body.dict())

    assert response.status_code == HTTPStatus.CREATED

    result = AddService(**response.json())

    assert result == body

    return ServiceWithApikey(**response.json())
