from fastapi import FastAPI

from .settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Legal OS API", version="0.1.0")

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
        }

    return app


app = create_app()
