"""
Health check and readiness route.
"""

import sqlite3
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Returns backend readiness, database connection status, and model artifact availability.
    """
    db_status = "uninitialized"
    if settings.DATABASE_PATH.exists():
        try:
            conn = sqlite3.connect(str(settings.DATABASE_PATH))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM drugs;")
            count = cursor.fetchone()[0]
            conn.close()
            db_status = f"connected ({count} drugs cataloged)"
        except Exception as e:
            db_status = f"error: {str(e)}"

    vec_path = settings.MODELS_DIR / "sentiment_vectorizer.joblib"
    model_path = settings.MODELS_DIR / "sentiment_model.joblib"
    models_loaded = vec_path.exists() and model_path.exists()

    return {
        "status": "healthy",
        "database": db_status,
        "models_loaded": models_loaded,
        "version": "1.0.0",
        "project": settings.PROJECT_NAME,
    }
