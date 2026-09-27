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
