"""
Pydantic schemas for sentiment analysis endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SentimentAnalysisRequest(BaseModel):
    text: str = Field(default="", description="Patient review text to analyze")


class SentimentAnalysisResponse(BaseModel):
    predicted_sentiment: str
    polarity_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    top_keywords: List[str] = Field(default_factory=list)
