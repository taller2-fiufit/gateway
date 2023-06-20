from typing import Any
from httpx import AsyncClient
from http import HTTPStatus

from src.api.model.service import (
    AddService,
    PatchService,
    Service,
    ServiceWithApikey,
)


async def test_services_get_empty(check_empty_services: None) -> None:
    # NOTE: all checks are located inside the check_empty_services fixture
    pass


async def test_services_post(created_body: ServiceWithApikey) -> None:
    # NOTE: all checks are located inside the created_body fixture
    pass


async def test_services_post_no_body(client: AsyncClient) -> None:
    response = await client.post("/services")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_services_post_duplicated_name(
    created_body: ServiceWithApikey, client: AsyncClient
) -> None:
    body = AddService(**created_body.dict())
    response = await client.post("/services", json=body.dict())

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {
        "detail": f'A service with the name "{body.name}" already exists'
    }


async def test_services_post_get(
    check_empty_services: None,
    created_body: ServiceWithApikey,
    client: AsyncClient,
) -> None:
    response = await client.get("/services")
    assert response.status_code == HTTPStatus.OK
    json = response.json()
    assert len(json) == 1

    got = Service(**json[0])
    expected = Service(**created_body.dict())

    assert got == expected

    response = await client.get("/services/count")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"count": 1}


async def test_services_patch(
    created_body: ServiceWithApikey, client: AsyncClient
) -> None:
    new_body = Service(**created_body.dict())

    new_body.blocked = True
    response = await client.patch(
        f"/services/{created_body.id}",
        json=PatchService(blocked=True).dict(),
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == new_body.dict()

    new_body.name = "new name"
    response = await client.patch(
        f"/services/{created_body.id}",
        json=PatchService(name="new name").dict(),
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == new_body.dict()


async def assert_invalid(body: dict[str, Any], client: AsyncClient) -> None:
    response_post = await client.post("/services", json=body)
    assert response_post.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    response_patch = await client.patch("/services/1", json=body)
    assert response_patch.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_services_invalid_body(
    created_body: ServiceWithApikey, client: AsyncClient
) -> None:
    body = AddService(**created_body.dict())
    body.name = "other name"

    # NOTE: we edit the dict because the model types contain validations
    d = body.dict()

    # too long name
    await assert_invalid({**d, "name": "a" * 32}, client)

    # short name
    await assert_invalid({**d, "name": ""}, client)

    # too long url
    await assert_invalid({**d, "url": "a" * 256}, client)

    # too long path
    await assert_invalid({**d, "path": "a" * 256}, client)

    # invalid path regex
    await assert_invalid({**d, "path": ")"}, client)


async def test_services_delete(
    created_body: ServiceWithApikey, client: AsyncClient
) -> None:
    body = Service(**created_body.dict())

    response = await client.get("/services")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == [body]

    response = await client.get(f"/services/{body.id}")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == body

    response = await client.delete(f"/services/{body.id}")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == body

    response = await client.get("/services")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []

    response = await client.get(f"/services/{body.id}")
    assert response.status_code == HTTPStatus.NOT_FOUND
