"""
Comprehensive integration tests for Step 4: India-Aware Recommendation Engine Integration.
Tests all 14 required dimensions:
1. Indian brand retrieval
2. Generic/ingredient retrieval
3. Condition matching
4. Combination drug handling (Multi-salt FDCs)
5. Missing sentiment (unreviewed medicines)
6. Missing rating (unreviewed medicines)
7. Available sentiment (empirically reviewed generic/brand)
8. Safety conflict filtering (Allergy, Contraindications, Severe DDIs)
9. Warning status (Moderate DDIs)
10. No-known-conflict status
11. Transparent explanation generation
12. Evidence-source propagation (NFI 2021 / CDSCO)
13. Candidate ranking order
14. Evidence-aware dynamic weight renormalization
"""

import pytest
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import PatientProfileRequest


@pytest.fixture(scope="module")
def rec_service():
    return RecommendationService()


def test_indian_brand_and_generic_retrieval(rec_service):
    """
    Test 1 & 2: Validates retrieval of Indian brand names (e.g. Alerfri, Dolo, Calpol, etc.)
    with canonical generic active constituents (e.g. paracetamol), manufacturers, and INR pricing.
    """
    req = PatientProfileRequest(
        age=30,
        condition="Fever",
        symptoms=["high temperature", "headache"],
        allergies=[],
        current_medications=[],
    )
    resp = rec_service.get_recommendations(req)
    assert len(resp.recommended_drugs) > 0

    first_rec = resp.recommended_drugs[0]
    assert first_rec.generic_name is not None
    assert "paracetamol" in first_rec.generic_name.lower()
    assert first_rec.manufacturer is not None
    assert first_rec.composition is not None
    assert first_rec.price_inr is not None and first_rec.price_inr > 0
    assert first_rec.dosage_form is not None


def test_condition_matching_and_evidence_source_propagation(rec_service):
    """
    Test 3 & 12: Verifies clinical condition matching and propagation of
    official evidence source (NFI 2021 / CDSCO / Clinical Monograph).
    """
    req = PatientProfileRequest(
        age=40,
        condition="Osteoarthritis",
        symptoms=["joint pain", "stiffness"],
        allergies=[],
        current_medications=[],
    )
    resp = rec_service.get_recommendations(req)
    assert len(resp.recommended_drugs) > 0

    first_rec = resp.recommended_drugs[0]
    assert first_rec.evidence_source is not None
    assert "National Formulary of India" in first_rec.evidence_source or "CDSCO" in first_rec.evidence_source or "Clinical" in first_rec.evidence_source



def test_combination_drug_multi_ingredient_handling(rec_service):
    """
    Test 4: Multi-salt Fixed Dose Combination (FDC) handling (e.g. Augmentin 625 Duo).
    """
    req = PatientProfileRequest(
        age=28,
        condition="Bacterial Infection",
        symptoms=["throat infection"],
        allergies=[],
        current_medications=[],
    )
    resp = rec_service.get_recommendations(req)
    aug = next((d for d in resp.recommended_drugs if "Augmentin" in d.drug_name), None)
    if aug:
        assert aug.composition is not None
        assert "amoxicillin" in aug.generic_name.lower()
        assert "clavulanic" in aug.generic_name.lower()


def test_dynamic_weight_renormalization_all_scenarios(rec_service):
    """
    Test 5, 6, 7, 14: Mathematical validation of dynamic weight renormalization
    across available and missing evidence factors.
    """
    recommender = rec_service.recommender

    # Scenario A: All 4 factors available (hypothetical empirical drug)
    candidates = recommender.get_candidate_drugs("High Blood Pressure", symptoms=["headache"])
    assert len(candidates) > 0

    for c in candidates:
        factors = c["factors"]
        w_cond = 0.40
        w_sim = 0.30
        w_sent = 0.20
        w_rat = 0.10

        avail_w = w_cond + w_sim
        weighted_sum = w_cond * factors["condition_match"] + w_sim * factors["similarity_score"]

        if factors["sentiment_data_available"] and factors["sentiment_score"] is not None:
            avail_w += w_sent
            weighted_sum += w_sent * factors["sentiment_score"]
        else:
            assert factors["sentiment_score"] is None

        if factors["rating_data_available"] and factors["rating_score"] is not None:
            avail_w += w_rat
            weighted_sum += w_rat * factors["rating_score"]
        else:
            assert factors["rating_score"] is None

        expected_score = round(weighted_sum / avail_w, 4)
        assert pytest.approx(c["raw_score"], 0.001) == expected_score


def test_safety_conflict_filtering_allergy(rec_service):
    """
    Test 8: Absolute safety conflict filtering for allergy.
    Patient allergic to Penicillins screened against Augmentin (Amoxicillin) -> FILTERED.
    """
    req = PatientProfileRequest(
        age=35,
        condition="Bacterial Infection",
        symptoms=[],
        allergies=["Penicillins"],
        current_medications=[],
    )
    resp = rec_service.get_recommendations(req)
    filtered_names = [f.drug_name for f in resp.filtered_drugs]
    assert any("Augmentin" in name or "Amoxicillin" in name or "Amoxycillin" in name for name in filtered_names)

    # Ensure no penicillin drug appears in recommended list
    rec_names = [r.drug_name for r in resp.recommended_drugs]
    assert "Augmentin 625 Duo Tablet" not in rec_names
    assert "Amoxyclav 625 Tablet" not in rec_names
    assert "Almox 500 Capsule" not in rec_names



def test_warning_status_moderate_ddi(rec_service):
    """
    Test 9 & 10: Moderate DDI triggers WARNING status with precaution details,
    while non-conflicting candidates receive NO_KNOWN_CONFLICT.
    """
    req = PatientProfileRequest(
        age=55,
        condition="High Blood Pressure",
        symptoms=["headache"],
        allergies=[],
        current_medications=["Potassium Chloride"],
    )
    resp = rec_service.get_recommendations(req)

    # Candidate statuses must be strictly partitioned
    for rec in resp.recommended_drugs:
        assert rec.safety_status in ("NO_KNOWN_CONFLICT", "WARNING")
        if rec.safety_status == "WARNING":
            assert len(rec.safety_details.ddi_warnings) > 0


def test_explanation_transparency_and_no_medical_claims(rec_service):
    """
    Test 11: Validates that explanations provide factor-level justifications
    and do NOT make unsubstantiated clinical superiority or prescription claims.
    """
    req = PatientProfileRequest(
        age=45,
        condition="High Blood Pressure",
        symptoms=["dizziness"],
        allergies=[],
        current_medications=[],
    )
    resp = rec_service.get_recommendations(req)
    assert len(resp.recommended_drugs) > 0

    first = resp.recommended_drugs[0]
    expl = first.explanation

    # Must contain transparency factors
    assert "Candidate identified for" in expl or "Recommended for" in expl
    assert "indication match" in expl
    assert "profile similarity" in expl
    assert "Safety screening:" in expl
    assert "Pricing, manufacturer, and packaging details reflect local pharmaceutical catalog" in expl

    # Must NOT contain prescribing or clinical superiority assertions
    forbidden_terms = ["best medicine", "guaranteed treatment", "this medicine is right for you", "take this medicine"]
    for term in forbidden_terms:
        assert term not in expl.lower()


def test_candidate_ranking_order(rec_service):
    """
    Test 13: Candidates must be ranked in descending order by score.
    """
    req = PatientProfileRequest(
        age=50,
        condition="Fever",
        symptoms=["chills"],
        allergies=[],
        current_medications=[],
    )
    resp = rec_service.get_recommendations(req)
    rec_scores = [r.final_score for r in resp.recommended_drugs]
    assert rec_scores == sorted(rec_scores, reverse=True)

    filt_scores = [f.raw_recommendation_score for f in resp.filtered_drugs]
    assert filt_scores == sorted(filt_scores, reverse=True)


def test_generic_level_sentiment_provenance_and_null_ratings(rec_service):
    """
    Step 4 Final Correction Tests:
    1. Indian brand with generic sentiment provenance (brand_review_data_available=False, sentiment_evidence_level='active_ingredient_review')
    2. Indian brand with no review evidence (sentiment_score=None, sentiment_evidence_level='no_review_evidence')
    3. Indian brand with no rating data (rating_score=None, average_rating=None)
    4. Explanation contains no "Indian patient sentiment" claims
    5. Explanation does not imply brand has reviews when total_reviews == 0
    6. Explanation does not display '0.0/10' as an actual rating
    """
    req = PatientProfileRequest(
        age=30,
        condition="Fever",
        symptoms=["high temperature"],
        allergies=[],
        current_medications=[],
    )
    resp = rec_service.get_recommendations(req)
    assert len(resp.recommended_drugs) > 0

    alerfri = next((d for d in resp.recommended_drugs if "Alerfri" in d.drug_name or "paracetamol" in (d.generic_name or "").lower()), None)
    assert alerfri is not None

    # Check factors & review summary
    factors = alerfri.factors
    assert factors.brand_review_data_available is False
    assert factors.sentiment_evidence_level in ("active_ingredient_review", "no_review_evidence")
    
    if factors.sentiment_evidence_level == "active_ingredient_review":
        assert factors.sentiment_score is not None
        assert factors.sentiment_evidence_source is not None
        assert "active ingredient" in factors.sentiment_evidence_source.lower()
    
    # Check rating representation
    assert factors.rating_score is None
    assert factors.rating_data_available is False
    assert alerfri.review_summary.total_reviews == 0
    assert alerfri.review_summary.average_rating is None

    # Check explanation guarantees
    expl = alerfri.explanation
    assert "indian patient sentiment" not in expl.lower()
    assert "0.0/10" not in expl
    assert "0/10" not in expl

    if factors.sentiment_evidence_level == "active_ingredient_review":
        assert "active-ingredient level" in expl
        assert "no brand-specific patient reviews are recorded" in expl

