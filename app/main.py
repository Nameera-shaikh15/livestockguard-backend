import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.database import init_db
from app.api import (
    routes_health,
    routes_animals,
    routes_analysis,
    routes_alerts,
    routes_dashboard,
    routes_assistant,
    routes_demo
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("livestockguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing LivestockGuard AI SQLite database...")
    init_db()
    logger.info("Database initialized successfully.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "LivestockGuard AI - AI-Assisted Multimodal Livestock Health Early-Warning System Backend MVP. "
        "Strict Non-Diagnostic Policy: Identifies risk signals, abnormal behavior, and environmental stressors without prescribing medication or disease diagnosis."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Exception Handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "message": "An unexpected server error occurred during analysis processing.",
            "details": str(exc) if settings.DEBUG else None
        }
    )


# Register Routers
app.include_router(routes_health.router)
app.include_router(routes_animals.router)
app.include_router(routes_analysis.router)
app.include_router(routes_alerts.router)
app.include_router(routes_dashboard.router)
app.include_router(routes_assistant.router)
app.include_router(routes_demo.router)
