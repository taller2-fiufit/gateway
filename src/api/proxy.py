import asyncio
import re
from http import HTTPStatus
from typing import Annotated, Any, List, Tuple
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from httpx import URL, AsyncClient, Response as SvcResp

from src.api.aliases import SessionDep
from src.auth import get_raw_token, optional_token
from src.db.session import SessionLocal
from src.logging import info, error
from src.db.utils import get_session
from src.db import services as services_db
import src.db.tokens as tokens_db


APIKEY_HEADER = "X-Apikey"
REGEN_DELAY = 1  # seconds


router = APIRouter(
    dependencies=[Depends(get_session), Depends(optional_token)],
)

ServiceInfo = Tuple[str, str]  # (url, apikey)
RoutingTable = List[Tuple[re.Pattern[str], ServiceInfo]]

routing_table: RoutingTable = []


@router.delete("/tokens", tags=["Auth"])
async def logout(
    session: SessionDep,
    response: Response,
    token: Annotated[dict[str, Any], get_raw_token],
    request: Request,
) -> Response:
    await tokens_db.invalidate_token(
        session, token["sub"], token["iat"], token["exp"]
    )
    await proxy(session, request.url.path, response, request)
    response.status_code = HTTPStatus.OK
    return response


def specificity(path: str) -> int:
    return sum(c not in r".\\[]()*?+" for c in path)


async def build_routing_table() -> RoutingTable:
    async with SessionLocal() as session:
        svcs = await services_db.get_all_services_inner(session, blocked=False)

    # NOTE: svc.path and url are never None even if mypy says otherwise
    table = list(map(lambda svc: (svc.path, (svc.url, svc.apikey)), svcs))
    table.sort(key=lambda pu: specificity(pu[0]))
    return [(re.compile(path), info) for (path, info) in table]


async def regenerate_routing_table() -> None:
    global routing_table
    try:
        while True:
            routing_table = await build_routing_table()
            await asyncio.sleep(REGEN_DELAY)
    except asyncio.CancelledError:  # task was cancelled
        return


def launch_routing_table_generator() -> asyncio.Task[Any]:
    return asyncio.create_task(regenerate_routing_table())


async def forward_request(svc_info: ServiceInfo, req: Request) -> SvcResp:
    svc_url, svc_apikey = svc_info

    headers = dict(req.headers)
    # content-length should be set according to request length
    headers.pop("content-length", None)
    # host should be set according to requested host
    headers.pop("host", None)

    # add apikey
    headers[APIKEY_HEADER] = svc_apikey

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

    svc_response.headers.pop(APIKEY_HEADER, None)
    return svc_response


async def get_routing_table() -> RoutingTable:
    return routing_table


async def proxy(
    session: SessionDep,
    path: str,
    response: Response,
    request: Request,
    table: RoutingTable = Depends(get_routing_table),
) -> Response:
    path = request.url.path
    svc_info = next(
        (info for (regex, info) in table if regex.fullmatch(path)),
        None,
    )
    if svc_info is None:
        response.status_code = HTTPStatus.NOT_FOUND
        return response

    info(f"Redirecting request to '{svc_info[0]}{path}'")

    try:
        svc_response = await forward_request(svc_info, request)
        response.body = svc_response.content
        response.status_code = svc_response.status_code
        return response
    except Exception as e:
        error(str(e))
        raise HTTPException(HTTPStatus.NOT_FOUND)


methods = ["GET", "PUT", "POST", "PATCH", "DELETE"]

router.add_api_route(
    "{path:path}", proxy, methods=methods, include_in_schema=False
)
