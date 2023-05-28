import uvicorn
import pytest
from typing import AsyncGenerator
from fastapi import FastAPI
from httpx import AsyncClient, Response
from http import HTTPStatus
from multiprocessing import Process

from src.api.model.service import AddService


MSG = "hello world!"
PORT = 26414

dummy_app = FastAPI()


@dummy_app.get("/hello")
async def get_hello() -> str:
    return MSG


@dummy_app.put("/hello")
async def put_hello() -> str:
    return MSG


@dummy_app.post("/hello")
async def post_hello() -> str:
    return MSG


@dummy_app.patch("/hello")
async def patch_hello() -> str:
    return MSG


@dummy_app.delete("/hello")
async def delete_hello() -> str:
    return MSG


def dummy_run() -> None:
    uvicorn.run(dummy_app, port=PORT)


@pytest.fixture()
async def dummy_server() -> AsyncGenerator[None, None]:
    proc = Process(target=dummy_run, args=(), daemon=True)
    proc.start()
    yield
    proc.kill()


def assert_method_works(response: Response) -> None:
    assert response.status_code == HTTPStatus.OK
    assert response.json() == MSG


async def test_proxy_various_methods(
    dummy_server: None, client: AsyncClient
) -> None:
    body = AddService(
        name="dummy service",
        url=f"http://localhost:{PORT}/",
        path="^/hello",
    )

    response = await client.post("/services", json=body.dict())
    assert response.status_code == HTTPStatus.CREATED

    assert_method_works(await client.get("/hello"))
    assert_method_works(await client.put("/hello"))
    assert_method_works(await client.post("/hello"))
    assert_method_works(await client.patch("/hello"))
    assert_method_works(await client.delete("/hello"))
