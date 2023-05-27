from logging import info
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import error
from src.api.model.service import AddService
from src.db.config import INITIAL_SERVICES
from src.db.session import SessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def parse_initial_services(
    initial_services: str,
) -> Generator[AddService, None, None]:
    # name,url,path -> AddService(name, url, path)
    for svc in initial_services.split(";"):
        if svc == "":
            continue

        svct = svc.split(",")

        if len(svct) != 3:
            error(f"Failed to parse entry: '{svc}'")
            continue

        name, url, path = svct
        info(f"Parsed service: name='{name}' url='{url}' path='{path}'")
        yield AddService(name=name, url=url, path=path)


def get_initial_services_gen() -> Generator[AddService, None, None]:
    info("Loading intial services configuration...")
    yield from parse_initial_services(INITIAL_SERVICES)
