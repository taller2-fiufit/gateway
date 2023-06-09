from http import HTTPStatus
from typing import List, Optional
from fastapi import APIRouter, Depends

from src.api.model.service import (
    AddService,
    PatchService,
    Service,
    ServiceCount,
    ServiceWithApikey,
)
from src.api.aliases import SessionDep
from src.auth import get_admin
from src.db.utils import get_session
from src.logging import info
from src.db import services as services_db


router = APIRouter(
    prefix="/services",
    tags=["Services"],
    # List of dependencies that get run ALWAYS for router and subrouters.
    # For a single-route dependency use the route decorator's parameter "dependencies"
    dependencies=[Depends(get_session), Depends(get_admin)],
)


@router.get("")
async def get_all_services(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
    blocked: Optional[bool] = None,
    up: Optional[bool] = None,
) -> List[Service]:
    """Get all services"""
    return await services_db.get_all_services(
        session, offset, limit, blocked, up
    )


@router.get("/count")
async def get_service_count(
    session: SessionDep,
    blocked: Optional[bool] = None,
) -> ServiceCount:
    """Get the number of services"""
    return await services_db.count_services(session, blocked)


@router.get("/{id}")
async def get_service(
    session: SessionDep,
    id: int,
) -> Service:
    """Get service by ID"""
    return await services_db.get_service(session, id)


@router.post("", status_code=HTTPStatus.CREATED)
async def add_service(
    session: SessionDep, service: AddService
) -> ServiceWithApikey:
    """Add a new service"""
    new_service = await services_db.add_service(session, service)
    info(f"Added a new service: {service}")
    return new_service


@router.patch("/{id}")
async def patch_service(
    session: SessionDep, id: int, service: PatchService
) -> Service:
    """Edit a service's info"""
    patched_service = await services_db.patch_service(session, id, service)
    info(f"Patched service: {patched_service}")
    return patched_service


@router.delete("/{id}")
async def delete_service(session: SessionDep, id: int) -> Service:
    """Delete a service"""
    deleted_service = await services_db.delete_service(session, id)
    info(f"Deleted service: {deleted_service}")
    return deleted_service
