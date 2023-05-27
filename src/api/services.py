from http import HTTPStatus
from typing import List
from fastapi import APIRouter, Depends

from src.api.model.service import (
    AddService,
    PatchService,
    Service,
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
) -> List[Service]:
    """Get all services"""
    # TODO: add query params
    return await services_db.get_all_services(session)


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
    """Add a new service"""
    patched_service = await services_db.patch_service(session, id, service)
    info(f"Patched service: {patched_service}")
    return patched_service
