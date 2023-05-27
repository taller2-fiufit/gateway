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
    app.dependency_overrides[get_user] = ignore_auth
    app.dependency_overrides[get_admin] = ignore_auth

    async with lifespan(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client


# -----------------
# SERVICES FIXTURES
# -----------------


@pytest.fixture
async def check_empty_services(client: AsyncClient) -> None:
    await assert_returns_empty(client, "/services")


@pytest.fixture
async def created_body(client: AsyncClient) -> ServiceWithApikey:
    body = AddService(
        name="test service", url="https://www.google.com/", path="^/google.*"
    )

    response = await client.post("/services", json=body.dict())

    assert response.status_code == HTTPStatus.CREATED

    result = AddService(**response.json())

    assert result == body

    return ServiceWithApikey(**response.json())
