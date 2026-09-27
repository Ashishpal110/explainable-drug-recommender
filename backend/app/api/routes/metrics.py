"""
Model and system evaluation metrics endpoint.
"""

import json
from pathlib import Path
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Model Evaluation & Metrics"])


@router.get("/model/metrics")
async def get_model_metrics():
    """
    Returns empirical evaluation metrics for the trained NLP sentiment model
    and recommendation system architecture specifications.
    """
    metrics_path = settings.MODELS_DIR / "sentiment_metrics.json"

    if metrics_path.exists():
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "model_evaluated": False,
        "sentiment_model": {
            "model_name": "TF-IDF + Logistic Regression",
            "supervision_method": "Rating-derived proxy labels (Pos >= 7, Neu 5-6, Neg <= 4)",
            "accuracy": None,
            "precision_macro": None,
            "recall_macro": None,
            "f1_macro": None,
            "classes": ["Negative", "Neutral", "Positive"],
            "evaluation_dataset_split": "Drugs.com Holdout Test Split (drugsComTest_raw.tsv)",
        },
        "recommendation_engine": {
            "algorithm": "Content-Based Cosine Similarity + Review Sentiment Weighting",
            "feature_representation": "TF-IDF Vector Space (Condition, Profile, Review Aspects)",
        },
    }
