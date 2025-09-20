from __future__ import annotations

import time
from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer

from .auth import decode_access_token
from .settings import Settings, get_settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    payload = decode_access_token(token, settings)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    roles = payload.get("roles", [])
    return {"username": username, "roles": roles}


def require_roles(*required_roles: str) -> Callable[[dict], dict]:
    def _checker(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        user_roles = set(user.get("roles", []))
        if not set(required_roles).issubset(user_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _checker


# Simple in-memory rate limiter keyed by client IP and path
_RATE_BUCKET: dict[tuple[str, str], list[float]] = {}


def rate_limit(max_requests: int, per_seconds: int) -> Callable[[Request], bool]:
    def _check(request: Request) -> bool:  # pragma: no cover - simple helper
        now = time.time()
        client_host = (
            request.client.host if request.client else "unknown"
        )
        key = (client_host, request.url.path)
        window = _RATE_BUCKET.setdefault(key, [])
        # prune outdated
        cutoff = now - per_seconds
        while window and window[0] < cutoff:
            window.pop(0)
        if len(window) >= max_requests:
            return False
        window.append(now)
        return True

    return _check


def apply_security_headers(
    request: Request, response: Response
) -> None:  # pragma: no cover - trivial
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'none'; frame-ancestors 'none'; form-action 'self'",
    )
