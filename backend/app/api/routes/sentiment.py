"""
Sentiment analysis endpoint.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.sentiment import SentimentAnalysisRequest, SentimentAnalysisResponse
from app.ml.sentiment import SentimentModel

router = APIRouter(prefix="/sentiment", tags=["Sentiment Analysis"])
sentiment_model = SentimentModel()


@router.post("/analyze", response_model=SentimentAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_sentiment(payload: SentimentAnalysisRequest) -> SentimentAnalysisResponse:
    """
    Analyzes arbitrary patient review text using the trained TF-IDF + Logistic Regression model.
    """
    try:
        result = sentiment_model.predict(payload.text)
        return SentimentAnalysisResponse(
            predicted_sentiment=result["predicted_sentiment"],
            polarity_score=result["polarity_score"],
            confidence=result["confidence"],
            top_keywords=result["top_keywords"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis error: {str(e)}",
        )
