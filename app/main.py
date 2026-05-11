from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import base, rooms
from app.settings import Settings
from app.ws import handler


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    app = FastAPI(title="Planning Poker API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(base.router)
    app.include_router(rooms.router)
    app.include_router(handler.router)

    return app
