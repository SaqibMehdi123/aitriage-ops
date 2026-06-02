"""FastAPI application factory.

Thin AI-services API for the foundation: health checks, the authenticated
`/me` context, and a `/jobs/ping` endpoint that proves the
API → Redis → worker → Postgres path. Feature routers (emails, drafts, rules,
knowledge, analytics) are added in later modules.
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import get_settings
from ..db import close_pool, get_pool
from ..logging import configure_logging, get_logger
from .routers import accounts, analytics, emails, health, knowledge, me, rules, webhooks
from .routers import settings as settings_router

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    get_pool()  # open the connection pool eagerly so first request is fast
    log.info("api_startup", env=get_settings().app_env)
    yield
    close_pool()
    log.info("api_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Inbox Triage + Reply Router API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Bind a request_id to every log line for cross-service tracing.
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers["x-request-id"] = request_id
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        log.error("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(accounts.router)
    app.include_router(webhooks.router)
    app.include_router(emails.router)
    app.include_router(knowledge.router)
    app.include_router(rules.router)
    app.include_router(analytics.router)
    app.include_router(settings_router.router)
    return app


app = create_app()
