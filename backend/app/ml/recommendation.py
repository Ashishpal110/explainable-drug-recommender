"""
Content-based recommendation engine for drug candidate discovery and scoring.
"""

import sqlite3
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import settings
from app.ml.sentiment import SentimentModel
from app.ml.preprocessing import normalize_condition_name


class ContentRecommender:
    """
    Content-based recommendation engine using condition matching, TF-IDF cosine similarity,
    model-inferred patient review sentiment, and rating scores.
    """

    def __init__(self, db_path: Optional[Union[Path, str]] = None, sentiment_model: Optional[SentimentModel] = None):
        self.db_path = Path(db_path) if db_path else settings.DATABASE_PATH
        self.sentiment_model = sentiment_model or SentimentModel()
        self.symptom_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.is_loaded = True

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def normalize_weights(self, weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        Validates and normalizes configurable heuristic recommendation weights.
        Default weights: condition_match=0.40, similarity=0.30, sentiment=0.20, rating=0.10.
        """
        defaults = {
            "condition_match": 0.40,
            "similarity": 0.30,
            "sentiment": 0.20,
            "rating": 0.10,
        }
        if not weights:
            return defaults

        w_cond = max(0.0, float(weights.get("condition_match", defaults["condition_match"])))
        w_sim = max(0.0, float(weights.get("similarity", defaults["similarity"])))
        w_sent = max(0.0, float(weights.get("sentiment", defaults["sentiment"])))
        w_rat = max(0.0, float(weights.get("rating", defaults["rating"])))

        total = w_cond + w_sim + w_sent + w_rat
        if total <= 0:
            return defaults

        return {
            "condition_match": round(w_cond / total, 4),
            "similarity": round(w_sim / total, 4),
            "sentiment": round(w_sent / total, 4),
            "rating": round(w_rat / total, 4),
        }

    CONDITION_ALIASES = {
        "hypertension": "High Blood Pressure",
        "htn": "High Blood Pressure",
        "high bp": "High Blood Pressure",
        "high blood pressure": "High Blood Pressure",
        "type 2 diabetes": "Diabetes, Type 2",
        "t2d": "Diabetes, Type 2",
        "type 1 diabetes": "Diabetes, Type 1",
        "t1d": "Diabetes, Type 1",
        "gerd": "GERD",
        "acid reflux": "GERD",
        "mdd": "Major Depressive Disorde",
    }

    def find_matching_condition(self, condition_query: str, cursor: sqlite3.Cursor) -> Optional[Tuple[int, str]]:
        """
        Resolves query condition to (condition_id, canonical_name).
        """
        clean_query = normalize_condition_name(condition_query)
        if not clean_query:
            return None

        # 0. Check alias dictionary
        target_query = self.CONDITION_ALIASES.get(clean_query.lower(), clean_query)

        # 1. Exact match (case-insensitive)
        cursor.execute("SELECT condition_id, name FROM conditions WHERE LOWER(name) = LOWER(?);", (target_query,))
        row = cursor.fetchone()
        if row:
            return row["condition_id"], row["name"]

        # 2. Substring match (condition contains query)
        cursor.execute("SELECT condition_id, name FROM conditions WHERE LOWER(name) LIKE LOWER(?) ORDER BY LENGTH(name) ASC LIMIT 1;", (f"%{target_query}%",))
        row = cursor.fetchone()
        if row:
            return row["condition_id"], row["name"]

        # 3. Reverse substring match (query contains condition name)
        cursor.execute("SELECT condition_id, name FROM conditions WHERE LOWER(?) LIKE '%' || LOWER(name) || '%' ORDER BY LENGTH(name) DESC LIMIT 1;", (target_query.lower(),))
        row = cursor.fetchone()
        if row:
            return row["condition_id"], row["name"]

        return None

    def calculate_symptom_similarity(self, symptoms: List[str], condition_name: str, drug_names: List[str]) -> List[float]:
        """
        Computes TF-IDF cosine similarity between symptom query and drug indication context.
        """
        if not symptoms or len(symptoms) == 0:
            # Baseline neutral similarity when no specific symptoms are provided
            return [0.50] * len(drug_names)

        query_text = f"{condition_name} " + " ".join(symptoms)
        corpus = [query_text] + [f"{d} {condition_name}" for d in drug_names]

        try:
            vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            tfidf_mat = vec.fit_transform(corpus)
            query_vec = tfidf_mat[0:1]
            drug_vecs = tfidf_mat[1:]
            sims = cosine_similarity(query_vec, drug_vecs)[0]
            # Map cosine range [-1, 1] / [0, 1] smoothly to [0.20, 1.00]
            scaled_sims = [float(np.clip(s * 0.5 + 0.5, 0.0, 1.0)) for s in sims]
            return scaled_sims
        except Exception:
            return [0.50] * len(drug_names)

    def get_candidate_drugs(
        self,
        condition: str,
        symptoms: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves candidate drugs for a condition, scores them via content-based features,
        and returns them ranked by raw recommendation score.
        """
        norm_weights = self.normalize_weights(weights)
        symptoms = symptoms or []

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            matched_condition = self.find_matching_condition(condition, cursor)
            if not matched_condition:
                return []

            condition_id, canonical_condition = matched_condition

            # Query all candidate drugs mapped to this condition
            cursor.execute(
                """
                SELECT 
                    d.drug_id,
                    d.name AS drug_name,
                    d.generic_name,
                    d.drug_class,
                    d.description,
                    d.avg_rating AS drug_avg_rating,
                    d.total_reviews AS drug_total_reviews,
                    d.positive_sentiment_ratio,
                    dc.review_count AS condition_review_count,
                    dc.avg_rating AS condition_avg_rating
                FROM drug_conditions dc
                JOIN drugs d ON dc.drug_id = d.drug_id
                WHERE dc.condition_id = ?
                ORDER BY dc.review_count DESC;
                """,
                (condition_id,),
            )
            rows = cursor.fetchall()
            if not rows:
                return []

            drug_names = [r["drug_name"] for r in rows]
            symptom_sims = self.calculate_symptom_similarity(symptoms, canonical_condition, drug_names)

            candidates = []
            for idx, row in enumerate(rows):
                drug_id = row["drug_id"]
                drug_name = row["drug_name"]
                drug_class = row["drug_class"] or "Not specified"
                generic_name = row["generic_name"]

                # 1. Condition Match Score (scaled by indication review volume)
                cond_review_cnt = row["condition_review_count"]
                condition_match = float(min(1.0, 0.80 + 0.20 * (min(cond_review_cnt, 50) / 50.0)))

                # 2. Similarity Score
                similarity_score = float(round(symptom_sims[idx], 4))

                # 3. Model-Inferred Sentiment Score
                sentiment_score = float(round(self.sentiment_model.get_drug_sentiment(drug_name), 4))

                # 4. Normalized Rating Score (1-10 scale mapped to [0.0, 1.0])
                avg_rating = row["condition_avg_rating"] or row["drug_avg_rating"] or 5.0
                rating_score = float(round(min(10.0, max(0.0, avg_rating)) / 10.0, 4))

                # 5. Composite Raw Recommendation Score
                raw_score = (
                    norm_weights["condition_match"] * condition_match
                    + norm_weights["similarity"] * similarity_score
                    + norm_weights["sentiment"] * sentiment_score
                    + norm_weights["rating"] * rating_score
                )
                raw_score = float(round(raw_score, 4))

                candidates.append({
                    "drug_id": drug_id,
                    "drug_name": drug_name,
                    "generic_name": generic_name,
                    "drug_class": drug_class,
                    "raw_score": raw_score,
                    "factors": {
                        "condition_match": round(condition_match, 4),
                        "similarity_score": round(similarity_score, 4),
                        "sentiment_score": round(sentiment_score, 4),
                        "rating_score": round(rating_score, 4),
                    },
                    "review_summary": {
                        "positive_ratio": round(float(row["positive_sentiment_ratio"] or 0.0), 4),
                        "total_reviews": int(row["drug_total_reviews"] or 0),
                        "average_rating": round(float(avg_rating), 2),
                        "condition_review_count": int(cond_review_cnt),
                    },
                })

            # Sort descending by raw recommendation score
            candidates.sort(key=lambda x: x["raw_score"], reverse=True)
            return candidates

        finally:
            conn.close()
