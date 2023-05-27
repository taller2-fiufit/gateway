from httpx import AsyncClient
from http import HTTPStatus


async def assert_returns_empty(client: AsyncClient, url: str) -> None:
    response = await client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == []
