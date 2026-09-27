"""
Pydantic schemas for recommendation requests and responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RecommendationWeights(BaseModel):
    condition_match: float = Field(default=0.40, ge=0.0, le=1.0)
    similarity: float = Field(default=0.30, ge=0.0, le=1.0)
    sentiment: float = Field(default=0.20, ge=0.0, le=1.0)
    rating: float = Field(default=0.10, ge=0.0, le=1.0)


class PatientProfileRequest(BaseModel):
    age: int = Field(..., ge=0, le=125, description="Patient age in years")
    condition: str = Field(..., min_length=1, description="Primary medical condition or diagnosis")
    symptoms: List[str] = Field(default_factory=list, description="Optional reported symptoms")
    allergies: List[str] = Field(default_factory=list, description="Known allergen or drug classes")
    current_medications: List[str] = Field(default_factory=list, description="Active medications currently taken")
    weights: Optional[RecommendationWeights] = Field(default_factory=RecommendationWeights)


class FactorScores(BaseModel):
    condition_match: float = Field(..., ge=0.0, le=1.0)
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    sentiment_score: float = Field(..., ge=0.0, le=1.0)
    rating_score: float = Field(..., ge=0.0, le=1.0)


class ReviewSummary(BaseModel):
    positive_ratio: float = Field(..., ge=0.0, le=1.0)
    total_reviews: int = Field(..., ge=0)
    average_rating: float = Field(..., ge=0.0, le=10.0)


class SafetyDetails(BaseModel):
    allergy_conflict: bool = False
    ddi_warnings: List[Dict[str, Any]] = Field(default_factory=list)
    contraindications: List[Dict[str, Any]] = Field(default_factory=list)


class RecommendedDrug(BaseModel):
    drug_id: int
    drug_name: str
    generic_name: Optional[str] = None
    drug_class: str
    final_score: float
    factors: FactorScores
    review_summary: ReviewSummary
    safety_status: str  # NO_KNOWN_CONFLICT or WARNING
    safety_details: SafetyDetails
    explanation: str


class FilteredDrug(BaseModel):
    drug_id: int
    drug_name: str
    raw_recommendation_score: float
    factors: FactorScores
    safety_status: str  # FILTERED_SAFETY_CONFLICT
    exact_rule_triggered: str
    affected_items: List[str]
    severity: str  # HIGH, CRITICAL
    clinical_reason: str
    explanation: str


class RecommendationResponse(BaseModel):
    patient_summary: Dict[str, Any]
    applied_weights: RecommendationWeights
    recommended_drugs: List[RecommendedDrug]
    filtered_drugs: List[FilteredDrug]
    disclaimer: str
