import time
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.model.token import DBToken


async def token_was_invalidated(
    session: AsyncSession,
    sub: int,
    iat: int,
) -> bool:
    invalidated_token = await session.scalar(
        select(DBToken).filter_by(user_id=sub, iat=iat).limit(1)
    )
    return invalidated_token is not None


async def invalidate_token(
    session: AsyncSession,
    sub: int,
    iat: int,
    exp: int,
) -> None:
    async with session.begin():
        await clean_up_old_entries(session)

        token = DBToken(sub=sub, iat=iat, exp=exp)

        session.add(token)


async def clean_up_old_entries(
    session: AsyncSession,
) -> None:
    """
    Deletes entries already past their expiration date.
    Doesn't commit changes to database.
    """
    await session.execute(
        delete(DBToken).where(DBToken.exp < int(time.time()))
    )
