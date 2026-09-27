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
        factors: Dict[str, Any],
        review_summary: Dict[str, Any],
        safety_status: str,
        safety_details: Dict[str, Any],
        evidence_source: Any = None,
        generic_name: Any = None,
        composition: Any = None,
    ) -> str:
        """
        Builds an evidence-grounded factor-level explanation for a recommended or warning candidate.
        """
        cond_match = int(factors.get("condition_match", 0.0) * 100)
        sim_score = int(factors.get("similarity_score", 0.0) * 100)
        sent_val = factors.get("sentiment_score")
        rat_val = factors.get("rating_score")
        sent_available = factors.get("sentiment_data_available", False) and (sent_val is not None)
        rat_available = factors.get("rating_data_available", False) and (rat_val is not None)

        parts = []

        # 1. Indication & Evidence Source
        evidence_txt = f" (Evidence: {evidence_source})" if evidence_source else ""
        if generic_name:
            parts.append(
                f"Candidate identified for {condition} based on active ingredient ({generic_name}){evidence_txt} with {cond_match}% indication match and {sim_score}% profile similarity."
            )
        else:
            parts.append(
                f"Candidate identified for {condition}{evidence_txt} with {cond_match}% indication match and {sim_score}% profile similarity."
            )

        # 2. Patient Sentiment & Review Evidence Distinction
        sent_level = factors.get("sentiment_evidence_level", "no_review_evidence")
        avg_rating = review_summary.get("average_rating")
        tot_reviews = review_summary.get("total_reviews", 0)

        if sent_level == "brand_review" and sent_available:
            sent_score = int(sent_val * 100)
            rating_txt = f" (avg satisfaction rating: {avg_rating}/10 across {tot_reviews:,} verified reviews)" if avg_rating is not None else ""
            parts.append(
                f"Brand-specific review analysis indicates {sent_score}% model-inferred positive satisfaction probability{rating_txt}."
            )
        elif sent_level == "active_ingredient_review" and sent_available:
            sent_score = int(sent_val * 100)
            parts.append(
                f"Review-derived sentiment evidence is available at the active-ingredient level ({generic_name or 'active constituent'}, {sent_score}% positive satisfaction probability) from the clinical drug-review corpus; no brand-specific patient reviews are recorded for this commercial formulation."
            )
        else:
            parts.append(
                "No empirical patient review records are associated with this formulation; sentiment factor was unassigned and scoring was dynamically renormalized across available clinical evidence."
            )


        # 3. Safety Screening Details
        if safety_status == "WARNING":
            warnings = safety_details.get("ddi_warnings", [])
            ddi_names = [w.get("interacting_drug_name") for w in warnings if w.get("interacting_drug_name")]
            parts.append(
                f"PRECAUTION (WARNING): Potential moderate interaction caution detected with concurrent medication(s): {', '.join(ddi_names) if ddi_names else 'active therapy'}. Clinical monitoring advised."
            )
        else:
            parts.append(
                "Safety screening: No matching allergy, contraindication, or major drug-drug interaction conflict detected in the local database."
            )

        # 4. Pharmaceutical Catalog Metadata Note
        parts.append(
            "Note: Pricing, manufacturer, and packaging details reflect local pharmaceutical catalog listings and do not constitute clinical efficacy or superiority claims."
        )

        return " ".join(parts)

    @staticmethod
    def generate_filtered_explanation(
        drug_name: str,
        safety_audit: Dict[str, Any],
        composition: Any = None,
    ) -> str:
        """
        Builds an exact explanation for a filtered unsafe candidate.
        """
        exact_rule = safety_audit.get("exact_rule_triggered", "SAFETY_CONFLICT")
        affected = safety_audit.get("affected_items", [])
        clinical_reason = safety_audit.get("clinical_reason", "Conflict with patient safety profile.")

        comp_txt = f" [{composition}]" if composition else ""
        explanation = (
            f"FILTERED DUE TO CRITICAL SAFETY CONFLICT ({exact_rule.replace('_', ' ')}): "
            f"{drug_name}{comp_txt} conflicts with {', '.join(affected)}. {clinical_reason}"
        )
        return explanation

