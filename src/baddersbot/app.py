from fastapi import FastAPI

from .routes import allocation, availability, dashboard, users
from .services.db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="Baddersbot Admin Portal", version="0.1.0")

    init_db()

    app.include_router(dashboard.router)
    app.include_router(availability.router)
    app.include_router(allocation.router)
    app.include_router(users.router)

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        """Simple liveness probe."""
        return {"status": "ok"}

    return app


app = create_app()
