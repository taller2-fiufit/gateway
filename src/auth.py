import os
import hashlib
import base64
import secrets
from http import HTTPStatus
from typing import Annotated, Any, Optional
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError

import src.db.tokens as tokens_db
from src.api.aliases import SessionDep

_AUTH_SECRET = os.getenv("AUTH_SECRET")
AUTH_SECRET = _AUTH_SECRET if _AUTH_SECRET is not None else ""

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="https://svc-users-fedecolangelo.cloud.okteto.net/tokens",
)

optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="https://svc-users-fedecolangelo.cloud.okteto.net/tokens",
    auto_error=False,
)


class User(BaseModel):
    email: str
    id: int
    admin: bool


def parse_token(token: str) -> dict[str, Any]:
    try:
        user_info = jwt.decode(
            token,
            AUTH_SECRET,
            algorithms="HS256",
            options={"verify_sub": False},
        )
    except (JWTError, ExpiredSignatureError, JWTClaimsError):
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED, "Token is invalid or has expired"
        )
    return user_info


async def check_if_token_was_invalidated(
    session: AsyncSession, parsed_token: dict[str, Any]
) -> None:
    sub = parsed_token["sub"]
    iat = parsed_token["iat"]

    if await tokens_db.token_was_invalidated(session, sub, iat):
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED, "Token is invalid or has expired"
        )


async def optional_token(
    token: Annotated[Optional[str], Depends(optional_oauth2_scheme)],
    session: SessionDep,
) -> Optional[User]:
    """Validates token and extracts user information"""
    if token is None:
        return None

    info = parse_token(token)

    await check_if_token_was_invalidated(session, info)

    return User(email=info["email"], id=info["sub"], admin=info["admin"])


async def get_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
) -> User:
    """Validates token and extracts user information"""
    info = parse_token(token)
    await check_if_token_was_invalidated(session, info)
    return User(**info)


async def get_admin(user: Annotated[User, Depends(get_user)]) -> User:
    """Validates that the user is an admin, and returns the user"""
    if not user.admin:
        raise HTTPException(
            HTTPStatus.FORBIDDEN, "Action requires admin permissions"
        )
    return user


DUMMY_ADMIN = User(email="dummy@example.com", id=1, admin=True)


async def ignore_auth() -> User:
    """Used for tests without authentication"""
    return DUMMY_ADMIN


APIKEY_LEN = 32
SALT_LEN = 16
SCRYPT_PARAMS = {"n": 2**12, "r": 16, "p": 1, "dklen": 64}


def generate_apikey() -> str:
    return secrets.token_urlsafe(APIKEY_LEN)


def generate_salt() -> bytes:
    return secrets.token_bytes(SALT_LEN)


def hash_apikey(apikey: str, salt: bytes) -> bytes:
    b_apikey = base64.urlsafe_b64decode(apikey + "=")  # add needed padding
    return hashlib.scrypt(b_apikey, salt=salt, **SCRYPT_PARAMS)
