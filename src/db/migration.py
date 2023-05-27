import logging
from time import sleep
from typing import Callable

from alembic.config import Config
from alembic import command
from sqlalchemy import Connection

from src.logging import error, debug
from src.db.session import engine


def run_upgrade(conn: Connection, config: Config) -> None:
    debug("upgrading database.")
    config.attributes["connection"] = conn
    command.upgrade(config, "head")


def run_downgrade(conn: Connection, config: Config) -> None:
    debug("resetting database.")
    config.attributes["connection"] = conn
    command.downgrade(config, "base")


async def run_alembic_cmd(
    cmd: Callable[[Connection, Config], None], retry: bool = False
) -> None:
    while True:
        try:
            async with engine.begin() as conn:
                alembic_cfg = Config("alembic.ini")
                await conn.run_sync(cmd, alembic_cfg)
                break
        except Exception as e:
            error(f"failed to upgrade. {e}")
            if not retry:
                break
            sleep(1)

    # re-enable logging, as alembic seems to disable it ¯\_(ツ)_/¯
    for logger in logging.root.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.disabled = False


async def upgrade_db() -> None:
    """Upgrade DB via 'alembic upgrade head'"""
    await run_alembic_cmd(run_upgrade, retry=True)


async def downgrade_db() -> None:
    """Downgrade DB via 'alembic downgrade base"""
    await run_alembic_cmd(run_downgrade, retry=False)
