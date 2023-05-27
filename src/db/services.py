from http import HTTPStatus
from typing import List, Optional
from fastapi import HTTPException
from secrets import token_urlsafe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import re

from src.api.model.service import (
    AddService,
    PatchService,
    Service,
    ServiceWithApikey,
)
from src.db.model.service import DBService


async def get_all_services(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 100,
    blocked: Optional[bool] = None,
) -> List[Service]:
    """Returns all existing services"""
    query = select(DBService)

    if blocked is not None:
        query = query.filter_by(blocked=blocked)

    res = await session.scalars(query.offset(offset).limit(limit))
    services = res.all()

    return list(map(Service.from_orm, services))


async def check_name_is_unique(session: AsyncSession, name: str) -> None:
    service = await session.scalar(select(DBService).filter_by(name=name))
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
    check_is_valid_regex(service.path or ")")  # path is never None

    apikey = token_urlsafe(32)
    new_service = DBService(apikey=apikey, **service.dict())

    async with session.begin():
        await check_name_is_unique(session, new_service.name)
        session.add(new_service)

    return ServiceWithApikey.from_orm(new_service)


async def patch_service(
    session: AsyncSession, id: int, patch: PatchService
) -> Service:
    """Updates the service's info"""
    check_is_valid_regex(patch.path or "")

    async with session.begin():
        service = await session.get(DBService, id)

        if service is None:
            raise HTTPException(HTTPStatus.NOT_FOUND, "Training not found")

        if patch.name is not None and patch.name != service.name:
            await check_name_is_unique(session, patch.name)

        service.update(**patch.dict())

        session.add(service)

    return Service.from_orm(service)
