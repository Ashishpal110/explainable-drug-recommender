"""
Safety-Aware Ranking & Explainability Service.
Generates transparent factor decompositions and human-readable natural language justifications.
"""

from typing import Dict, Any


class ExplanationService:
    """
    Generates transparent, deterministic explanations for recommended and filtered drug candidates.
    """

    @staticmethod
    def generate_recommendation_explanation(
        drug_name: str,
        condition: str,
        factors: Dict[str, float],
        review_summary: Dict[str, Any],
        safety_status: str,
        safety_details: Dict[str, Any],
    ) -> str:
        """
        Builds a factor-level explanation for a recommended or warning drug.
        """
        cond_match = int(factors["condition_match"] * 100)
        sim_score = int(factors["similarity_score"] * 100)
        sent_score = int(factors["sentiment_score"] * 100)
        avg_rating = review_summary.get("average_rating", 0.0)

        parts = [
            f"Recommended for {condition}: Condition match factor contributes {cond_match}%, with {sim_score}% profile similarity.",
            f"Patient review analysis indicates {sent_score}% model-inferred positive sentiment (avg satisfaction rating: {avg_rating}/10 across {review_summary.get('total_reviews', 0):,} reviews).",
        ]

        if safety_status == "WARNING":
            warnings = safety_details.get("ddi_warnings", [])
            ddi_names = [w.get("interacting_drug_name") for w in warnings]
            parts.append(f"PRECAUTION (WARNING): Moderate interaction caution with concurrent medication(s): {', '.join(ddi_names)}. Monitoring advised.")
        else:
            parts.append("Safety screening: No matching allergy or drug-drug interaction conflict detected in the local database.")

        return " ".join(parts)

    @staticmethod
    def generate_filtered_explanation(
        drug_name: str,
        safety_audit: Dict[str, Any],
    ) -> str:
        """
        Builds an exact explanation for a filtered unsafe candidate.
        """
        exact_rule = safety_audit.get("exact_rule_triggered", "SAFETY_CONFLICT")
        affected = safety_audit.get("affected_items", [])
        clinical_reason = safety_audit.get("clinical_reason", "Conflict with patient safety profile.")

        explanation = (
            f"FILTERED DUE TO CRITICAL SAFETY CONFLICT ({exact_rule.replace('_', ' ')}): "
            f"{drug_name} conflicts with {', '.join(affected)}. {clinical_reason}"
        )
        return explanation
