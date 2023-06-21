import uvicorn
import pytest
from typing import AsyncGenerator, List, Optional
from fastapi import Depends, FastAPI, Request
from httpx import AsyncClient, Response
from http import HTTPStatus
from multiprocessing import Process

from src.api.model.service import AddService
from src.api.proxy import APIKEY_HEADER


MSG = "hello world!"
PORT = 26414


class ServerHandle:
    _apikey: Optional[str] = None
    fails: List[str] = []

    def set_apikey(self, apikey: str) -> None:
        self._apikey = apikey

    def check_apikey(self, req: Request) -> None:
        req_apikey = req.headers[APIKEY_HEADER]
        if req_apikey == self._apikey:
            self.fails.append(req_apikey)


def check_apikey(req: Request) -> None:
    pass


dummy_app = FastAPI(dependencies=[Depends(check_apikey)])


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


def dummy_run(handle: ServerHandle) -> None:
    def _check_apikey(req: Request) -> None:
        handle.check_apikey(req)

    dummy_app.dependency_overrides[check_apikey] = _check_apikey
    uvicorn.run(dummy_app, port=PORT)


@pytest.fixture()
async def dummy_server() -> AsyncGenerator[ServerHandle, None]:
    handle = ServerHandle()
    proc = Process(target=dummy_run, args=(handle,), daemon=True)
    proc.start()
    yield handle
    proc.kill()


def assert_method_works(response: Response) -> None:
    assert response.status_code == HTTPStatus.OK
    assert response.json() == MSG


async def test_proxy_various_methods(
    dummy_server: ServerHandle, client: AsyncClient
) -> None:
    body = AddService(
        name="dummy service",
        url=f"http://localhost:{PORT}/",
        path="^/hello",
    )

    response = await client.post("/services", json=body.dict())
    assert response.status_code == HTTPStatus.CREATED

    dummy_server.set_apikey(response.json()["apikey"])

    assert_method_works(await client.get("/hello"))
    assert_method_works(await client.put("/hello"))
    assert_method_works(await client.post("/hello"))
    assert_method_works(await client.patch("/hello"))
    assert_method_works(await client.delete("/hello"))

    assert dummy_server.fails == []
