"""
Drug recommendation endpoint.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.recommendation import PatientProfileRequest, RecommendationResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter(tags=["Recommendation"])
recommendation_service = RecommendationService()


@router.post("/recommend", response_model=RecommendationResponse, status_code=status.HTTP_200_OK)
async def generate_recommendations(profile: PatientProfileRequest) -> RecommendationResponse:
    """
    Generates personalized, explainable drug candidates for a patient condition profile
    while running deterministic safety screening against recorded allergies, active medications, and contraindications.
    """
    try:
        return recommendation_service.get_recommendations(profile)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}",
        )
