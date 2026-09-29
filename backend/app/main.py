import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .core.config import settings
from .database.connection import SessionLocal, engine
from .routers import api_router
from .seed import seed

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Alembic is the schema manager. Startup fails clearly if migrations were not applied.
    try:
        with engine.connect() as connection:
            current_revision = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise RuntimeError("Database migrations are missing; run `alembic upgrade head` from backend/") from exc
    if current_revision is None:
        raise RuntimeError("Database has no applied Alembic revision; run `alembic upgrade head` from backend/")
    if settings.environment == "development":
        with SessionLocal() as db:
            seed(db)
    yield


app = FastAPI(title="University Management System API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.info("Constraint conflict for %s %s", request.method, request.url.path)
    return JSONResponse(status_code=409, content={"detail": "The change conflicts with existing data"})


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled API error for %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
