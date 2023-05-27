import re
from http import HTTPStatus
from typing import Annotated, List, Tuple
from fastapi import APIRouter, Depends, Request, Response
from httpx import URL, AsyncClient, Response as SvcResp
from sqlalchemy.ext.asyncio import AsyncSession
from cachetools.func import ttl_cache

from src.api.aliases import SessionDep
from src.logging import info
from src.db.utils import get_session
from src.db import services as services_db


router = APIRouter(
    dependencies=[Depends(get_session)],
)

RoutingTable = List[Tuple[re.Pattern[str], str]]
TableDep = Annotated[RoutingTable, Depends(get_session)]


def specificity(path: str) -> int:
    return sum(c not in r".\\[]()*?+" for c in path)


@ttl_cache(maxsize=1, ttl=4)
async def get_routing_table(session: AsyncSession) -> RoutingTable:
    svcs = await services_db.get_all_services(session)
    # NOTE: svc.path and url are never None even if mypy says otherwise
    table = list(map(lambda svc: (svc.path or "", svc.url or ""), svcs))
    table.sort(key=lambda pu: specificity(pu[0]))
    return [(re.compile(path), url) for (path, url) in table]


async def forward_request(svc_url: str, req: Request) -> SvcResp:
    headers = dict(req.headers)
    # content-length should be set according to request length
    headers.pop("content-length", None)
    # host should be set according to requested host
    headers.pop("host", None)

    url = URL(path=req.url.path, query=req.url.query.encode("utf-8"))
    content = req.stream()

    async with AsyncClient(base_url=svc_url) as client:
        svc_req = client.build_request(
            req.method,
            url=url,
            headers=headers,
            cookies=req.cookies,
            content=content,
        )
        svc_response = await client.send(svc_req)

    return svc_response


async def proxy(
    session: SessionDep, path: str, response: Response, request: Request
) -> Response:
    path = request.url.path
    routing_table = await get_routing_table(session)
    url = next(
        (url for (regex, url) in routing_table if regex.fullmatch(path)), None
    )
    if url is None:
        response.status_code = HTTPStatus.NOT_FOUND
        return response

    info(f"Redirecting request to '{url}{path}'")

    svc_response = await forward_request(url, request)

    response.body = svc_response.content
    response.status_code = svc_response.status_code
    return response


router.add_api_route("{path:path}", proxy, include_in_schema=False)
