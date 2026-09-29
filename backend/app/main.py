import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .core.config import settings
from .database.connection import Base, engine, get_db
from .routers import api_router
from .seed import seed

logger = logging.getLogger(__name__)
app = FastAPI(title="University Management System API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    if settings.environment == "development":
        with next(get_db()) as db:
            seed(db)
@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled API error for %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
