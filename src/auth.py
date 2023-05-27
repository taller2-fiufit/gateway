from http import HTTPStatus
import os
from typing import Annotated
from fastapi import Depends, HTTPException

from pydantic import BaseModel
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError

from fastapi.security import OAuth2PasswordBearer

_AUTH_SECRET = os.getenv("AUTH_SECRET")
AUTH_SECRET = _AUTH_SECRET if _AUTH_SECRET is not None else ""

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="https://svc-users-fedecolangelo.cloud.okteto.net/tokens",
)


class User(BaseModel):
    email: str
    sub: int
    admin: bool


async def get_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """Validates token and extracts user information"""
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

    return User(**user_info)


async def get_admin(user: Annotated[User, Depends(get_user)]) -> User:
    """Validates that the user is an admin, and returns the user"""
    if not user.admin:
        raise HTTPException(
            HTTPStatus.FORBIDDEN, "Action requires admin permissions"
        )
    return user


DUMMY_ADMIN = User(email="dummy@example.com", sub=1, admin=True)


async def ignore_auth() -> User:
    """Used for tests without authentication"""
    return DUMMY_ADMIN
