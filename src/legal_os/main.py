from typing import Annotated, Callable, Awaitable

import time
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, Request

from .settings import Settings, get_settings
from .dependencies import apply_security_headers, rate_limit, require_roles
from .logging_config import configure_json_logging, set_request_id
from .routers import auth as auth_router
from .routers import upload as upload_router
from .routers import metadata as metadata_router
from .routers import sessions as sessions_router
from .routers import quality as quality_router
from .routers import docling as docling_router
from .db import ping_database
from .routers import langextract as langextract_router
from .routers import qa as qa_router
from .routers import orchestrator as orchestrator_router
from .routers import compliance as compliance_router
from .routers import review as review_router
from .routers import groundedness as groundedness_router
from .routers.citation import router as citation_router
from .routers import recovery as recovery_router
from .routers import documents as documents_router
from .routers import akn as akn_router
from .routers import akn_query as akn_query_router
from .routers import consistency as consistency_router


_APP_START_MONOTONIC = time.monotonic()
_APP_START_ISO = datetime.now(timezone.utc).isoformat()
_REQUEST_COUNT = 0


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    # Validate configuration early to fail-fast on invalid env setups
    settings.assert_valid()
    app = FastAPI(title="Legal OS API", version="0.1.0")
    configure_json_logging()
    # Ensure dependencies using get_settings receive this instance
    app.dependency_overrides[get_settings] = lambda: settings

    # Security headers middleware
    @app.middleware("http")
    async def _security_headers_mw(
        request: Request, call_next: Callable[[Request], Awaitable]
    ) -> object:  # pragma: no cover - simple
        response = await call_next(request)
        apply_security_headers(request, response)
        return response

    # Correlation ID + timing middleware and request counting
    @app.middleware("http")
    async def _correlation_and_timing_mw(
        request: Request, call_next: Callable[[Request], Awaitable]
    ) -> object:  # pragma: no cover - simple
        import logging
        import uuid

        logger = logging.getLogger("request")
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(req_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            _ = int((time.perf_counter() - start) * 1000)
            logger.exception(
                "request_error",
            )
            set_request_id(None)
            raise
        _ = int((time.perf_counter() - start) * 1000)
        logger.info(
            "request_completed",
        )
        response.headers.setdefault("X-Request-ID", req_id)
        set_request_id(None)
        global _REQUEST_COUNT
        _REQUEST_COUNT += 1
        return response

    def _uptime_seconds() -> int:
        return int(time.monotonic() - _APP_START_MONOTONIC)

    def _app_info() -> dict[str, object]:
        return {
            "status": "ok",
            "name": settings.app_name,
            "version": app.version,
            "env": settings.env,
            "started_at": _APP_START_ISO,
            "uptime_seconds": _uptime_seconds(),
            "requests": _REQUEST_COUNT,
        }

    @app.get("/health/live")
    async def liveness() -> dict[str, object]:  # pragma: no cover - trivial
        # Liveness should not depend on external services
        data = _app_info()
        data["status"] = "live"
        return data

    @app.get("/health/ready")
    async def readiness_v2() -> dict[str, object]:  # pragma: no cover - trivial path
        # Readiness includes dependency checks (DB, etc.)
        db_ok = ping_database()
        return {
            **_app_info(),
            "status": "ready" if db_ok else "degraded",
            "dependencies": {
                "database": "ok" if db_ok else "fail",
            },
        }

    # Backwards-compat simple endpoints
    @app.get("/health")
    async def health() -> dict[str, str]:  # pragma: no cover - trivial
        return {"status": "ok"}

    @app.get("/readiness")
    async def readiness() -> dict[str, str]:  # pragma: no cover - trivial
        # In future, add checks for DB, storage, and external services
        db_ok = ping_database()
        return {"status": "ready" if db_ok else "degraded"}

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
    app.include_router(upload_router.router)
    app.include_router(metadata_router.router)
    app.include_router(sessions_router.router)
    app.include_router(quality_router.router)
    app.include_router(docling_router.router)
    app.include_router(langextract_router.router)
    app.include_router(qa_router.router)
    app.include_router(orchestrator_router.router)
    app.include_router(compliance_router.router)
    app.include_router(review_router.router)
    app.include_router(groundedness_router.router)
    app.include_router(citation_router, prefix="/api/v1", tags=["citations"])
    app.include_router(recovery_router.router)
    app.include_router(documents_router.router)
    app.include_router(akn_router.router)
    app.include_router(akn_query_router.router)
    app.include_router(consistency_router.router)

    return app


app = create_app()
