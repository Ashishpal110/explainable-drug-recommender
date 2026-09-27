"""
Safety-Aware Recommendation Orchestration Service.
Coordinates content-based recommendation scoring with independent deterministic safety screening.
"""

from pathlib import Path
from typing import Optional, Union
from app.core.config import settings
from app.ml.sentiment import SentimentModel
from app.ml.recommendation import ContentRecommender
from app.safety.screening import SafetyScreeningEngine
from app.services.explanation_service import ExplanationService
from app.schemas.recommendation import (
    PatientProfileRequest,
    RecommendationResponse,
    RecommendedDrug,
    FilteredDrug,
    FactorScores,
    ReviewSummary,
    SafetyDetails,
    RecommendationWeights,
)


DISCLAIMER_TEXT = (
    "This is an academic research and decision-support prototype. "
    "The status NO_KNOWN_CONFLICT indicates only that no matching rule was triggered in the local database "
    "and does NOT establish clinical safety. This system does not provide medical advice or replace a qualified healthcare professional."
)


class RecommendationService:
    """
    Orchestrates candidate retrieval, scoring, safety filtering, and ranking.
    """

    def __init__(
        self,
        db_path: Optional[Union[Path, str]] = None,
        models_dir: Optional[Path] = None,
    ):
        self.db_path = Path(db_path) if db_path else settings.DATABASE_PATH
        self.models_dir = Path(models_dir) if models_dir else settings.MODELS_DIR
        self.sentiment_model = SentimentModel(models_dir=self.models_dir)
        self.recommender = ContentRecommender(db_path=self.db_path, sentiment_model=self.sentiment_model)
        self.safety_engine = SafetyScreeningEngine(db_path=self.db_path)
        self.explanation_service = ExplanationService()

    def get_recommendations(self, profile: PatientProfileRequest) -> RecommendationResponse:
        """
        Processes a patient profile:
        1. Retrieves condition-matched candidates scored via ContentRecommender
        2. Independently screens each candidate through SafetyScreeningEngine
        3. Partitions candidates into recommended (NO_KNOWN_CONFLICT / WARNING) and filtered (FILTERED_SAFETY_CONFLICT)
        4. Synthesizes transparent natural language explanations and factor breakdowns
        """
        weights_dict = profile.weights.model_dump() if profile.weights else None
        applied_weights_dict = self.recommender.normalize_weights(weights_dict)

        candidates = self.recommender.get_candidate_drugs(
            condition=profile.condition,
            symptoms=profile.symptoms,
            weights=applied_weights_dict,
        )

        recommended_drugs = []
        filtered_drugs = []

        for candidate in candidates:
            safety_audit = self.safety_engine.screen_candidate(
                candidate=candidate["drug_id"],
                age=profile.age,
                condition=profile.condition,
                allergies=profile.allergies,
                current_medications=profile.current_medications,
            )

            safety_status = safety_audit["safety_status"]

            if safety_status == "FILTERED_SAFETY_CONFLICT":
                filtered_expl = self.explanation_service.generate_filtered_explanation(
                    drug_name=candidate["drug_name"],
                    safety_audit=safety_audit,
                    composition=candidate.get("composition"),
                )
                filtered_drugs.append(
                    FilteredDrug(
                        drug_id=candidate["drug_id"],
                        drug_name=candidate["drug_name"],
                        brand_name=candidate.get("brand_name"),
                        generic_name=candidate.get("generic_name"),
                        composition=candidate.get("composition"),
                        manufacturer=candidate.get("manufacturer"),
                        dosage_form=candidate.get("dosage_form"),
                        price_inr=candidate.get("price_inr"),
                        raw_recommendation_score=candidate["raw_score"],
                        factors=FactorScores(**candidate["factors"]),
                        safety_status="FILTERED_SAFETY_CONFLICT",
                        exact_rule_triggered=safety_audit.get("exact_rule_triggered") or "CRITICAL_SAFETY_CONFLICT",
                        affected_items=safety_audit.get("affected_items", []),
                        severity=safety_audit.get("severity", "HIGH"),
                        clinical_reason=safety_audit.get("clinical_reason") or "Safety constraint violated.",
                        explanation=filtered_expl,
                    )
                )
            else:
                safety_details = SafetyDetails(
                    allergy_conflict=len(safety_audit.get("allergy_conflicts", [])) > 0,
                    ddi_warnings=safety_audit.get("ddi_warnings", []),
                    contraindications=safety_audit.get("contraindications", []),
                )
                rec_expl = self.explanation_service.generate_recommendation_explanation(
                    drug_name=candidate["drug_name"],
                    condition=profile.condition,
                    factors=candidate["factors"],
                    review_summary=candidate["review_summary"],
                    safety_status=safety_status,
                    safety_details=safety_details.model_dump(),
                    evidence_source=candidate.get("evidence_source"),
                    generic_name=candidate.get("generic_name"),
                    composition=candidate.get("composition"),
                )
                recommended_drugs.append(
                    RecommendedDrug(
                        drug_id=candidate["drug_id"],
                        drug_name=candidate["drug_name"],
                        brand_name=candidate.get("brand_name"),
                        generic_name=candidate.get("generic_name"),
                        drug_class=candidate.get("drug_class") or "Not specified",
                        composition=candidate.get("composition"),
                        manufacturer=candidate.get("manufacturer"),
                        dosage_form=candidate.get("dosage_form"),
                        pack_size=candidate.get("pack_size"),
                        price_inr=candidate.get("price_inr"),
                        condition=candidate.get("condition"),
                        evidence_source=candidate.get("evidence_source"),
                        final_score=candidate["raw_score"],
                        factors=FactorScores(**candidate["factors"]),
                        review_summary=ReviewSummary(
                            positive_ratio=candidate["review_summary"]["positive_ratio"],
                            total_reviews=candidate["review_summary"]["total_reviews"],
                            average_rating=candidate["review_summary"]["average_rating"],
                        ),
                        safety_status=safety_status,
                        safety_details=safety_details,
                        explanation=rec_expl,
                    )
                )


        # Sort recommendations and filtered drugs descending by score
        recommended_drugs.sort(key=lambda x: x.final_score, reverse=True)
        filtered_drugs.sort(key=lambda x: x.raw_recommendation_score, reverse=True)

        patient_summary = {
            "age": profile.age,
            "condition": profile.condition,
            "symptoms": profile.symptoms,
            "allergies": profile.allergies,
            "current_medications": profile.current_medications,
        }

        return RecommendationResponse(
            patient_summary=patient_summary,
            applied_weights=RecommendationWeights(**applied_weights_dict),
            recommended_drugs=recommended_drugs,
            filtered_drugs=filtered_drugs,
            disclaimer=DISCLAIMER_TEXT,
        )
