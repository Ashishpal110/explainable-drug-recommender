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

    def get_drug_sentiment_info(self, drug_name: str, generic_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns structured sentiment metadata with explicit provenance:
          - sentiment_score: Optional[float] (None if unreviewed)
          - sentiment_data_available: bool (False if unreviewed)
          - sentiment_evidence_level: 'brand_review' | 'active_ingredient_review' | 'no_review_evidence'
          - sentiment_evidence_source: Optional[str]
          - matched_entity: Optional[str]
        """
        if not drug_name:
            return {
                "sentiment_score": None,
                "sentiment_data_available": False,
                "sentiment_evidence_level": "no_review_evidence",
                "sentiment_evidence_source": None,
                "matched_entity": None,
            }

        # 1. Direct key lookup (Brand-specific)
        if drug_name in self.drug_sentiment_scores:
            return {
                "sentiment_score": round(float(self.drug_sentiment_scores[drug_name]), 4),
                "sentiment_data_available": True,
                "sentiment_evidence_level": "brand_review",
                "sentiment_evidence_source": "Brand-specific review corpus",
                "matched_entity": drug_name,
            }

        # 2. Case-insensitive match on trade name (Brand-specific)
        drug_name_lower = drug_name.strip().lower()
        for k, v in self.drug_sentiment_scores.items():
            if k.lower() == drug_name_lower:
                return {
                    "sentiment_score": round(float(v), 4),
                    "sentiment_data_available": True,
                    "sentiment_evidence_level": "brand_review",
                    "sentiment_evidence_source": "Brand-specific review corpus",
                    "matched_entity": k,
                }

        # 3. Canonical generic active ingredient lookup (including cross-pharmacopoeia synonyms)
        if generic_name:
            SYNONYMS = {
                "paracetamol": ["acetaminophen"],
                "acetaminophen": ["paracetamol"],
                "salbutamol": ["albuterol"],
                "albuterol": ["salbutamol"],
                "amoxycillin": ["amoxicillin"],
                "amoxicillin": ["amoxycillin"],
                "levosalbutamol": ["levalbuterol"],
                "levalbuterol": ["levosalbutamol"],
            }
            for part in generic_name.split("+"):
                part_clean = part.strip().lower()
                candidates_to_try = [part_clean] + SYNONYMS.get(part_clean, [])
                for target in candidates_to_try:
                    for k, v in self.drug_sentiment_scores.items():
                        if k.lower() == target:
                            return {
                                "sentiment_score": round(float(v), 4),
                                "sentiment_data_available": True,
                                "sentiment_evidence_level": "active_ingredient_review",
                                "sentiment_evidence_source": f"Clinical drug-review corpus (active ingredient: {target})",
                                "matched_entity": target,
                            }

        return {
            "sentiment_score": None,
            "sentiment_data_available": False,
            "sentiment_evidence_level": "no_review_evidence",
            "sentiment_evidence_source": None,
            "matched_entity": None,
        }

    def get_drug_sentiment(self, drug_name: str, generic_name: Optional[str] = None) -> Optional[float]:
        """
        Returns the model-inferred mean positive probability S_sentiment(d)
        aggregated across all verified reviews associated with the drug or its active generic salt.
        Returns None if no empirical patient review evidence exists (no synthetic priors assigned).
        """
        info = self.get_drug_sentiment_info(drug_name, generic_name)
        return info["sentiment_score"]


