from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME
    }


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": "hackathon-mvp",
        "non_diagnostic_guarantee": True
    }
