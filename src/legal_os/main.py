from typing import Annotated, Callable, Awaitable

from fastapi import Depends, FastAPI, Request

from .settings import Settings, get_settings
from .dependencies import apply_security_headers, rate_limit, require_roles
from .routers import auth as auth_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    # Validate configuration early to fail-fast on invalid env setups
    settings.assert_valid()
    app = FastAPI(title="Legal OS API", version="0.1.0")

    # Security headers middleware
    @app.middleware("http")
    async def _security_headers_mw(
        request: Request, call_next: Callable[[Request], Awaitable]
    ) -> object:  # pragma: no cover - simple
        response = await call_next(request)
        apply_security_headers(request, response)
        return response

    @app.get("/health")
    async def health() -> dict[str, str]:  # pragma: no cover - trivial
        return {"status": "ok"}

    @app.get("/readiness")
    async def readiness() -> dict[str, str]:  # pragma: no cover - trivial
        # In future, add checks for DB, storage, and external services
        return {"status": "ready"}

    @app.get("/config")
    async def config_echo() -> dict[str, str | int | bool]:
        # Safe subset of config to verify environments
        return {
            "env": settings.env,
            "debug": settings.debug,
            "app_name": settings.app_name,
            "flags.enable_pgvector": settings.flags.enable_pgvector,
        }

    # Protected example route with RBAC
    @app.get("/admin")
    async def admin_area(
        user: Annotated[dict, Depends(require_roles("admin"))]
    ) -> dict[str, str]:
        return {"hello": user["username"], "role": "admin"}

    # Rate-limited auth token endpoint wrapping (fast in-memory)
    @app.middleware("http")
    async def _rate_limit_mw(
        request: Request, call_next: Callable[[Request], Awaitable]
    ) -> object:  # pragma: no cover - simple
        if request.url.path == "/auth/token":
            limiter = rate_limit(max_requests=5, per_seconds=60)
            if not limiter(request):
                from fastapi.responses import JSONResponse

                return JSONResponse({"detail": "Too Many Requests"}, status_code=429)
        return await call_next(request)

    # Routers
    app.include_router(auth_router.router)

    return app


app = create_app()
