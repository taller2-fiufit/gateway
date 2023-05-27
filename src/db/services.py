import re
from http import HTTPStatus
from typing import List, Optional
from fastapi import HTTPException
from secrets import token_urlsafe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.model.service import (
    AddService,
    PatchService,
    Service,
    ServiceWithApikey,
)
from src.db.model.service import DBService
from src.db.session import SessionLocal
from src.db.status_updater import update_statuses
from src.db.utils import get_initial_services_gen
from src.logging import error, warn


async def add_initial_services() -> None:
    """Adds initial services, overwriting on name collision"""
    async with SessionLocal() as session:
        async with session.begin():
            for svc in get_initial_services_gen():
                try:
                    old = await get_service_by_name(session, svc.name or "")

                    if old is not None:
                        await session.delete(old)

                    _ = await _add_service_inner(session, svc)
                except HTTPException as e:
                    warn(str(e))
                except Exception as e:
                    error(str(e))


async def get_all_services(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 100,
    blocked: Optional[bool] = None,
    with_statuses: bool = True,
) -> List[Service]:
    """Returns all existing services"""
    query = select(DBService)

    if blocked is not None:
        query = query.filter_by(blocked=blocked)

    res = await session.scalars(query.offset(offset).limit(limit))
    services = list(map(Service.from_orm, res.all()))

    if with_statuses:
        await update_statuses(services)

    return services


async def get_service(
    session: AsyncSession,
    id: int,
) -> Service:
    db_service = await session.get(DBService, id)
    if db_service is None:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Service not found")

    return Service.from_orm(db_service)


async def get_service_by_name(
    session: AsyncSession, name: str
) -> Optional[DBService]:
    service = await session.scalar(select(DBService).filter_by(name=name))
    return service


async def check_name_is_unique(session: AsyncSession, name: str) -> None:
    service = await get_service_by_name(session, name)
    if service is not None:
        raise HTTPException(
            HTTPStatus.CONFLICT,
            f'A service with the name "{name}" already exists',
        )


def check_is_valid_regex(regex: str) -> None:
    try:
        _ = re.compile(regex)
    except re.error:
        raise HTTPException(HTTPStatus.UNPROCESSABLE_ENTITY)


async def add_service(
    session: AsyncSession, service: AddService
) -> ServiceWithApikey:
    """Adds a new service"""
    async with session.begin():
        new_service = await _add_service_inner(session, service)

    return ServiceWithApikey.from_orm(new_service)


async def _add_service_inner(
    session: AsyncSession, service: AddService
) -> DBService:
    check_is_valid_regex(service.path or ")")  # path is never None
    await check_name_is_unique(session, service.name or "")  # never None

    apikey = token_urlsafe(32)
    new_service = DBService(apikey=apikey, **service.dict())

    session.add(new_service)

    return new_service


async def patch_service(
    session: AsyncSession, id: int, patch: PatchService
) -> Service:
    """Updates the service's info"""
    check_is_valid_regex(patch.path or "")

    async with session.begin():
        service = await session.get(DBService, id)

        if service is None:
            raise HTTPException(HTTPStatus.NOT_FOUND, "Service not found")

        if patch.name is not None and patch.name != service.name:
            await check_name_is_unique(session, patch.name)

        service.update(**patch.dict())

        session.add(service)

    return Service.from_orm(service)
