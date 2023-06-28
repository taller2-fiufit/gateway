import re
import time
from http import HTTPStatus
from typing import Annotated, Any, List, Optional, Tuple
from fastapi import APIRouter, Depends, Request, Response
from httpx import URL, AsyncClient, Response as SvcResp
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.aliases import SessionDep
from src.auth import get_raw_token, optional_token
from src.logging import info
from src.db.utils import get_session
from src.db import services as services_db
import src.db.tokens as tokens_db


APIKEY_HEADER = "X-Apikey"


router = APIRouter(
    dependencies=[Depends(get_session), Depends(optional_token)],
)

ServiceInfo = Tuple[str, str]  # (url, apikey)
RoutingTable = List[Tuple[re.Pattern[str], ServiceInfo]]


@router.delete("/tokens", tags=["Auth"])
async def logout(
    session: SessionDep,
    response: Response,
    token: Annotated[dict[str, Any], get_raw_token]]
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


async def _get_routing_table(session: AsyncSession) -> RoutingTable:
    svcs = await services_db.get_all_services_inner(session, blocked=False)
    # NOTE: svc.path and url are never None even if mypy says otherwise
    table = list(map(lambda svc: (svc.path, (svc.url, svc.apikey)), svcs))
    table.sort(key=lambda pu: specificity(pu[0]))
    return [(re.compile(path), info) for (path, info) in table]


update_time: Optional[float] = 0.0
cached_routing_table: RoutingTable = []


async def get_routing_table(session: AsyncSession) -> RoutingTable:
    global update_time, cached_routing_table
    now = time.monotonic()
    if now > (update_time if update_time is not None else now):
        update_time = None  # lock so noone updates
        try:
            cached_routing_table = await _get_routing_table(session)
        except Exception:
            update_time = time.monotonic() + 1.0
            raise

    return cached_routing_table


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


async def proxy(
    session: SessionDep, path: str, response: Response, request: Request
) -> Response:
    path = request.url.path
    routing_table = await get_routing_table(session)
    svc_info = next(
        (info for (regex, info) in routing_table if regex.fullmatch(path)),
        None,
    )
    if svc_info is None:
        response.status_code = HTTPStatus.NOT_FOUND
        return response

    info(f"Redirecting request to '{svc_info[0]}{path}'")

    svc_response = await forward_request(svc_info, request)

    response.body = svc_response.content
    response.status_code = svc_response.status_code
    return response


methods = ["GET", "PUT", "POST", "PATCH", "DELETE"]

router.add_api_route(
    "{path:path}", proxy, methods=methods, include_in_schema=False
)
