"""
API v1 root router aggregation.
"""

from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.recommend import router as recommend_router
from app.api.routes.sentiment import router as sentiment_router
from app.api.routes.drugs import router as drugs_router
from app.api.routes.metrics import router as metrics_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(recommend_router)
api_router.include_router(sentiment_router)
api_router.include_router(drugs_router)
api_router.include_router(metrics_router)

__all__ = ["api_router"]
