"""FastAPI application entrypoint.

Serves REST and WebSocket endpoints; chat/ticket and WebSocket streaming (Task-008).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routes import chat as chat_routes
from api.routes import memory as memory_routes
from api.routes import sessions as sessions_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    import os
    settings = get_settings()
    logger.info("Starting Support Co-Pilot API (env=%s)", settings.environment)
    # Langfuse: set env so get_client() picks up credentials
    if settings.langfuse_secret_key and settings.langfuse_public_key:
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
        os.environ.setdefault("LANGFUSE_BASE_URL", settings.langfuse_base_url)
        logger.info("Langfuse observability enabled")
    yield
    try:
        from tools.langfuse_observability import flush_langfuse
        flush_langfuse()
    except Exception:
        pass
    logger.info("Shutting down Support Co-Pilot API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title="Intelligent Support & Incident Co-Pilot API",
        description="Collaborative agent system for support and operations.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["Health"])
    async def health():
        """Health check for load balancers and Docker."""
        return {"status": "ok", "service": "support-co-pilot-api"}

    app.include_router(memory_routes.router, prefix="/api")
    app.include_router(chat_routes.router, prefix="/api")
    app.include_router(sessions_routes.router, prefix="/api")

    return app


app = create_app()
