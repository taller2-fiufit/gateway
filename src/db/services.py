import re
from http import HTTPStatus
from typing import List, Optional, Sequence
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.model.service import (
    AddService,
    PatchService,
    Service,
    ServiceCount,
    ServiceWithApikey,
)
from src.auth import generate_apikey
from src.db.model.service import DBService
from src.db.session import SessionLocal
from src.db.status_updater import update_statuses
from src.db.utils import get_initial_services_gen
from src.logging import error, warn, info


async def add_initial_services() -> None:
    """Adds initial services, overwriting on name collision"""
    async with SessionLocal() as session:
        async with session.begin():
            for svc in get_initial_services_gen():
                try:
                    old = await get_service_by_name(session, svc.name or "")

                    if old is not None:
                        old.update(**svc.dict())
                        await session.commit()
                    else:
                        _, key = await _add_service_inner(session, svc)
                        info(
                            f"Added initial service '{svc.name}' with key '{key}'"
                        )
                except HTTPException as e:
                    warn(str(e))
                except Exception as e:
                    error(str(e))


async def get_all_services_inner(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 100,
    blocked: Optional[bool] = None,
) -> Sequence[DBService]:
    """Returns all services in DB"""
    query = select(DBService)

    if blocked is not None:
        query = query.filter_by(blocked=blocked)

    res = await session.scalars(query.offset(offset).limit(limit))

    return res.all()


async def get_all_services(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 100,
    blocked: Optional[bool] = None,
    up: Optional[bool] = None,
) -> List[Service]:
    """Returns all existing services with their status"""
    db_services = await get_all_services_inner(session, offset, limit, blocked)
    services = list(map(Service.from_orm, db_services))

    await update_statuses(services)

    if up is not None:
        services = [s for s in services if s.up == up]

    return services


async def count_services(
    session: AsyncSession,
    blocked: Optional[bool] = None,
) -> ServiceCount:
    """Counts the number of services"""
    query = select(func.count()).select_from(DBService)

    if blocked is not None:
        query = query.filter_by(blocked=blocked)

    count = (await session.scalar(query)) or 0

    return ServiceCount(count=count)


async def get_service(
    session: AsyncSession,
    id: int,
) -> Service:
    db_service = await session.get(DBService, id)

    if db_service is None:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Service not found")

    service = Service.from_orm(db_service)

    await update_statuses([service])

    return service


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
    new_service, apikey = await _add_service_inner(session, service)

    added_service = ServiceWithApikey.from_orm(new_service)
    added_service.apikey = apikey

    return added_service


async def _add_service_inner(
    session: AsyncSession, service: AddService
) -> tuple[DBService, str]:
    check_is_valid_regex(service.path or ")")  # path is never None
    await check_name_is_unique(session, service.name or "")  # never None

    apikey = generate_apikey()

    new_service = DBService(apikey=apikey, **service.dict())

    session.add(new_service)
    await session.commit()

    return new_service, apikey


async def patch_service(
    session: AsyncSession, id: int, patch: PatchService
) -> Service:
    """Updates the service's info"""
    check_is_valid_regex(patch.path or "")

    service = await session.get(DBService, id)

    if service is None:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Service not found")

    if patch.name is not None and patch.name != service.name:
        await check_name_is_unique(session, patch.name)

    service.update(**patch.dict())

    session.add(service)

    return Service.from_orm(service)


async def delete_service(session: AsyncSession, id: int) -> Service:
    """Deletes a service"""
    service = await session.get(DBService, id)

    if service is None:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Service not found")

    await session.delete(service)

    return Service.from_orm(service)
