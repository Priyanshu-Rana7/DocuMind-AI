from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="System Health Check")
def health_check(db: Session = Depends(get_db)):
    """
    Check API service and database connectivity.
    """
    db_status = "healthy"
    migration_status = "unknown"
    try:
        db.execute(text("SELECT 1"))
        try:
            migration_status = db.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none() or "not_initialized"
        except Exception:
            migration_status = "not_initialized"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    llm_configured = (
        settings.LLM_PROVIDER == "mock"
        or bool(settings.OPENROUTER_API_KEY)
    )
    ocr_configured = settings.OCR_PROVIDER in {"mock", "easyocr", "tesseract"}

    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "migration": migration_status,
        "ocr_provider": settings.OCR_PROVIDER,
        "ocr_configured": ocr_configured,
        "poppler_configured": bool(settings.POPPLER_PATH),
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.OPENROUTER_MODEL,
        "llm_configured": llm_configured,
        "storage_provider": settings.STORAGE_PROVIDER,
        "storage_configured": (
            settings.STORAGE_PROVIDER == "local"
            or bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)
        ),
    }
