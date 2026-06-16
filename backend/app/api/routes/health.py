from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "application_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "api_version": "v1"
    }
