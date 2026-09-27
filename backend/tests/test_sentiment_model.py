"""
Unit tests for the NLP sentiment model inference wrapper.
"""

import pytest
from app.ml.sentiment import SentimentModel


@pytest.fixture(scope="module")
def sentiment_model():
    model = SentimentModel()
    assert model.is_loaded, "Sentiment model artifacts should be trained and loaded."
    return model


def test_sentiment_model_loading(sentiment_model):
    assert sentiment_model.vectorizer is not None
    assert sentiment_model.classifier is not None
    assert sentiment_model.metrics is not None
    assert len(sentiment_model.drug_sentiment_scores) > 0


def test_sentiment_positive_prediction(sentiment_model):
    text = "This medication worked wonders! My symptoms completely disappeared and I feel amazing with zero side effects."
    result = sentiment_model.predict(text)
    assert result["predicted_sentiment"] == "Positive"
    assert 0.50 <= result["polarity_score"] <= 1.0
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["top_keywords"], list)


def test_sentiment_negative_prediction(sentiment_model):
    text = "Horrible experience. Caused severe nausea, extreme dizziness, and made my condition much worse. Avoid this drug."
    result = sentiment_model.predict(text)
    assert result["predicted_sentiment"] == "Negative"
    assert 0.0 <= result["polarity_score"] <= 0.50
    assert 0.0 <= result["confidence"] <= 1.0


def test_sentiment_empty_text(sentiment_model):
    result = sentiment_model.predict("")
    assert result["predicted_sentiment"] == "Neutral"
    assert result["polarity_score"] == 0.50


def test_get_drug_sentiment_known_and_unknown(sentiment_model):
    # Known drug in review training corpus
    score = sentiment_model.get_drug_sentiment("Amlodipine")
    assert score is not None
    assert 0.0 <= score <= 1.0

    # Unreviewed entity returns None (no synthetic priors assigned)
    unknown_score = sentiment_model.get_drug_sentiment("CompletelyUnknownDrugXYZ")
    assert unknown_score is None, "Unreviewed drugs must return None to prevent fabricating patient sentiment"

    # Test metadata helper
    info_known = sentiment_model.get_drug_sentiment_info("Amlodipine")
    assert info_known["sentiment_data_available"] is True
    assert isinstance(info_known["sentiment_score"], float)

    info_unknown = sentiment_model.get_drug_sentiment_info("CompletelyUnknownDrugXYZ")
    assert info_unknown["sentiment_data_available"] is False
    assert info_unknown["sentiment_score"] is None

