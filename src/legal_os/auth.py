from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict, cast, Callable

from jose import JWTError, jwt
from passlib.context import CryptContext

from .settings import Settings, get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bool(pwd_context.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    return str(pwd_context.hash(password))


def create_access_token(
    subject: str,
    *,
    settings: Optional[Settings] = None,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    settings = settings or get_settings()
    to_encode: dict[str, Any] = {"sub": subject}
    if extra_claims:
        to_encode.update(extra_claims)
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire})
    secret = settings.jwt_secret or "dev-secret"
    return str(jwt.encode(to_encode, secret, algorithm=settings.jwt_algorithm))


def decode_access_token(token: str, settings: Optional[Settings] = None) -> Dict[str, Any]:
    settings = settings or get_settings()
    secret = settings.jwt_secret or "dev-secret"
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
        return cast(Dict[str, Any], payload)
    except JWTError as e:  # pragma: no cover - pass through as generic error
        raise ValueError("Invalid token") from e


def require_document_permission(document_id_param: str, permission: str) -> Callable:
    """Dependency factory enforcing per-document permission based on user roles/claims.

    This uses a simple policy: admins always allowed; editors can write; viewers can read.
    Replace with DB-backed ACLs later.
    """

    from fastapi import Depends, HTTPException, Request
    # Local import to avoid circular dependency at module import time
    from .dependencies import require_roles

    def _dep(
        request: Request,
        user: dict = Depends(require_roles("viewer", "editor", "admin")),
    ) -> dict:
        doc_id = request.path_params.get(document_id_param)
        if doc_id is None:
            raise HTTPException(status_code=400, detail="Missing document id")
        role = user.get("role")
        if role == "admin":
            return user
        if permission in ("read",) and role in ("viewer", "editor"):
            return user
        if permission in ("write",) and role == "editor":
            return user
        raise HTTPException(status_code=403, detail="Forbidden: insufficient permissions")

    return _dep
