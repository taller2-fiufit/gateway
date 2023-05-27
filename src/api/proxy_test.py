import uvicorn
import pytest
from typing import AsyncGenerator
from fastapi import FastAPI
from httpx import AsyncClient
from http import HTTPStatus
from multiprocessing import Process

from src.api.model.service import AddService


MSG = "hello world!"
PORT = 26414

dummy_app = FastAPI()


@dummy_app.get("/hello")
async def hello() -> str:
    return MSG


def dummy_run() -> None:
    uvicorn.run(dummy_app, port=PORT)


@pytest.fixture()
async def dummy_server() -> AsyncGenerator[None, None]:
    proc = Process(target=dummy_run, args=(), daemon=True)
    proc.start()
    yield
    proc.kill()


async def test_services_post_duplicated_name(
    dummy_server: None, client: AsyncClient
) -> None:
    body = AddService(
        name="dummy service",
        url=f"http://localhost:{PORT}/",
        path="^/hello",
    )

    response = await client.post("/services", json=body.dict())
    assert response.status_code == HTTPStatus.CREATED

    response = await client.get("/hello")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == MSG
