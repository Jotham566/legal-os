from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..auth import create_access_token, get_password_hash, verify_password
from ..settings import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


# In-memory user store for demo/tests; replace with DB-backed user model later
class _User:
    def __init__(self, username: str, password_hash: str, roles: list[str]):
        self.username = username
        self.password_hash = password_hash
        self.roles = roles


_USERS: dict[str, _User] = {
    "admin": _User("admin", get_password_hash("admin"), ["admin", "user"]),
    "user": _User("user", get_password_hash("user"), ["user"]),
}


def authenticate_user(username: str, password: str) -> _User | None:
    user = _USERS.get(username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


@router.post("/token")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(
        subject=user.username,
        settings=settings,
        expires_delta=timedelta(minutes=settings.jwt_expire_minutes),
        extra_claims={"roles": user.roles},
    )
    return {"access_token": token, "token_type": "bearer"}
