"""
Unit tests for the content-based recommendation engine.
"""

import pytest
from app.ml.recommendation import ContentRecommender


@pytest.fixture(scope="module")
def recommender():
    return ContentRecommender()


def test_weight_normalization_defaults(recommender):
    weights = recommender.normalize_weights(None)
    assert weights["condition_match"] == 0.40
    assert weights["similarity"] == 0.30
    assert weights["sentiment"] == 0.20
    assert weights["rating"] == 0.10
    assert pytest.approx(sum(weights.values()), 0.001) == 1.0


def test_weight_normalization_custom(recommender):
    custom = {"condition_match": 2.0, "similarity": 2.0, "sentiment": 0.0, "rating": 0.0}
    weights = recommender.normalize_weights(custom)
    assert weights["condition_match"] == 0.50
    assert weights["similarity"] == 0.50
    assert weights["sentiment"] == 0.0
    assert weights["rating"] == 0.0
    assert pytest.approx(sum(weights.values()), 0.001) == 1.0


def test_get_candidates_known_condition(recommender):
    candidates = recommender.get_candidate_drugs(
        condition="Hypertension",
        symptoms=["high blood pressure", "headache"],
    )
    assert len(candidates) > 0

    first = candidates[0]
    assert "drug_id" in first
    assert "drug_name" in first
    assert "raw_score" in first
    assert 0.0 <= first["raw_score"] <= 1.0
    assert "factors" in first
    assert "condition_match" in first["factors"]
    assert "similarity_score" in first["factors"]
    assert "sentiment_score" in first["factors"]
    assert "rating_score" in first["factors"]

    # Verify descending sort order
    scores = [c["raw_score"] for c in candidates]
    assert scores == sorted(scores, reverse=True)


def test_get_candidates_unknown_condition(recommender):
    candidates = recommender.get_candidate_drugs(condition="NonExistentAlienDisease999")
    assert candidates == []


def test_candidate_factors_and_evidence_aware_weight_renormalization(recommender):
    """
    Verifies that candidates return explicit data availability flags,
    and dynamically renormalize scoring weights across available evidence without fabricating data.
    """
    candidates = recommender.get_candidate_drugs(
        condition="Fever",
        symptoms=["high temperature"],
    )
    assert len(candidates) > 0

    for c in candidates:
        factors = c["factors"]
        assert "condition_match" in factors
        assert "similarity_score" in factors
        assert "sentiment_score" in factors
        assert "sentiment_data_available" in factors
        assert "rating_score" in factors
        assert "rating_data_available" in factors

        if factors["sentiment_data_available"]:
            assert isinstance(factors["sentiment_score"], float)
            assert 0.0 <= factors["sentiment_score"] <= 1.0
        else:
            assert factors["sentiment_score"] is None, "Unreviewed candidate must have sentiment_score=None"

        if factors["rating_data_available"]:
            assert isinstance(factors["rating_score"], float)
            assert 0.0 <= factors["rating_score"] <= 1.0
        else:
            assert factors["rating_score"] is None, "Unreviewed candidate must have rating_score=None"

        # Verify dynamic evidence-aware weight renormalization formula
        avail_weights = 0.40 + 0.30
        weighted_sum = 0.40 * factors["condition_match"] + 0.30 * factors["similarity_score"]

        if factors["sentiment_data_available"] and factors["sentiment_score"] is not None:
            avail_weights += 0.20
            weighted_sum += 0.20 * factors["sentiment_score"]

        if factors["rating_data_available"] and factors["rating_score"] is not None:
            avail_weights += 0.10
            weighted_sum += 0.10 * factors["rating_score"]

        expected_score = round(weighted_sum / avail_weights, 4)
        assert pytest.approx(c["raw_score"], 0.001) == expected_score


