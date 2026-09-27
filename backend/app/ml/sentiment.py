"""
NLP Sentiment Model interface and inference wrapper for patient drug reviews.
"""

import json
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.ml.preprocessing import clean_review_text


class SentimentModel:
    """
    Wrapper for the trained TF-IDF + Logistic Regression sentiment model.
    Evaluates patient satisfaction from review text using rating-derived proxy supervision.
    """

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = Path(models_dir) if models_dir else settings.MODELS_DIR
        self.vectorizer = None
        self.classifier = None
        self.metrics = None
        self.drug_sentiment_scores = {}
        self.is_loaded = False
        self._load_artifacts()

    def _load_artifacts(self):
        vec_path = self.models_dir / "sentiment_vectorizer.joblib"
        model_path = self.models_dir / "sentiment_model.joblib"
        metrics_path = self.models_dir / "sentiment_metrics.json"
        scores_path = self.models_dir / "drug_sentiment_scores.joblib"

        if vec_path.exists() and model_path.exists():
            self.vectorizer = joblib.load(vec_path)
            self.classifier = joblib.load(model_path)
            self.is_loaded = True

        if metrics_path.exists():
            with open(metrics_path, "r", encoding="utf-8") as f:
                self.metrics = json.load(f)

        if scores_path.exists():
            self.drug_sentiment_scores = joblib.load(scores_path)

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Infers sentiment from review text.
        Returns:
          - predicted_sentiment: 'Positive', 'Neutral', or 'Negative'
          - polarity_score: Predicted probability of positive class P(Positive | text) in [0.0, 1.0]
          - confidence: Highest predicted class probability
          - top_keywords: Top salient TF-IDF terms
        """
        if not self.is_loaded or self.vectorizer is None or self.classifier is None:
            raise RuntimeError("Sentiment model artifacts are not loaded. Run train_sentiment.py first.")

        cleaned = clean_review_text(text)
        if not cleaned:
            return {
                "predicted_sentiment": "Neutral",
                "polarity_score": 0.50,
                "confidence": 0.33,
                "top_keywords": [],
            }

        vec = self.vectorizer.transform([cleaned])
        pred_label = str(self.classifier.predict(vec)[0])
        probs = self.classifier.predict_proba(vec)[0]
        classes = list(self.classifier.classes_)

        pos_idx = classes.index("Positive") if "Positive" in classes else 0
        polarity_score = float(probs[pos_idx])
        confidence = float(np.max(probs))

        # Extract top salient features
        feature_names = np.array(self.vectorizer.get_feature_names_out())
        row_indices = vec.indices
        row_data = vec.data
        if len(row_data) > 0:
            top_order = np.argsort(row_data)[::-1][:5]
            top_keywords = feature_names[row_indices[top_order]].tolist()
        else:
            top_keywords = []

        return {
            "predicted_sentiment": pred_label,
            "polarity_score": round(polarity_score, 4),
            "confidence": round(confidence, 4),
            "top_keywords": top_keywords,
        }

    def get_drug_sentiment(self, drug_name: str) -> float:
        """
        Returns the model-inferred mean positive probability S_sentiment(d)
        aggregated across all reviews associated with the drug.
        """
        if not drug_name:
            return 0.50
        return float(self.drug_sentiment_scores.get(drug_name, 0.50))
