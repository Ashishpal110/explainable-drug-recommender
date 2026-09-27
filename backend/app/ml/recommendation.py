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

    def calculate_symptom_similarity(self, symptoms: List[str], condition_name: str, drug_contexts: List[Dict[str, Any]]) -> List[float]:
        """
        Computes TF-IDF cosine similarity between symptom query and drug indication context.
        """
        if not symptoms or len(symptoms) == 0:
            # Baseline neutral similarity when no specific symptoms are provided
            return [0.50] * len(drug_contexts)

        query_text = f"{condition_name} " + " ".join(symptoms)
        corpus = [query_text] + [
            f"{d['drug_name']} {d.get('generic_name') or ''} {d.get('composition') or ''} {condition_name}"
            for d in drug_contexts
        ]

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
            return [0.50] * len(drug_contexts)

    def get_candidate_drugs(
        self,
        condition: str,
        symptoms: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves candidate drugs for a condition from the Indian pharmaceutical catalog,
        scores them via evidence-grounded content features with dynamic weight renormalization,
        and returns them ranked by composite recommendation score.
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

            # Query candidate drugs mapped to this condition with Indian market metadata
            cursor.execute(
                """
                SELECT 
                    d.drug_id,
                    d.name AS drug_name,
                    d.generic_name,
                    d.drug_class,
                    d.description,
                    d.composition,
                    d.manufacturer,
                    d.price_inr,
                    d.dosage_form,
                    d.pack_size,
                    d.avg_rating AS drug_avg_rating,
                    d.total_reviews AS drug_total_reviews,
                    d.positive_sentiment_ratio,
                    dc.review_count AS condition_review_count,
                    dc.avg_rating AS condition_avg_rating,
                    dc.evidence_source,
                    dc.indication_type
                FROM drug_conditions dc
                JOIN drugs d ON dc.drug_id = d.drug_id
                WHERE dc.condition_id = ?
                ORDER BY (CASE WHEN d.manufacturer IS NOT NULL THEN 1 ELSE 0 END) DESC, dc.review_count DESC, d.avg_rating DESC, d.drug_id ASC
                LIMIT 200;
                """,
                (condition_id,),
            )
            rows = cursor.fetchall()
            if not rows:
                return []

            drug_contexts = [
                {
                    "drug_name": r["drug_name"],
                    "generic_name": r["generic_name"],
                    "composition": r["composition"],
                }
                for r in rows
            ]
            symptom_sims = self.calculate_symptom_similarity(symptoms, canonical_condition, drug_contexts)

            w_cond = norm_weights["condition_match"]
            w_sim = norm_weights["similarity"]
            w_sent = norm_weights["sentiment"]
            w_rat = norm_weights["rating"]

            candidates = []
            for idx, row in enumerate(rows):
                drug_id = row["drug_id"]
                drug_name = row["drug_name"]
                drug_class = row["drug_class"] or "Not specified"
                generic_name = row["generic_name"]
                composition = row["composition"]
                manufacturer = row["manufacturer"]
                dosage_form = row["dosage_form"] or "Not specified"
                pack_size = row["pack_size"]
                price_inr = float(row["price_inr"]) if row["price_inr"] is not None and row["price_inr"] > 0 else None
                evidence_source = row["evidence_source"]
                indication_type = row["indication_type"] or "Primary"

                # Extract normalized brand name if distinct from full trade name
                brand_name = drug_name
                if dosage_form and dosage_form.lower() in drug_name.lower():
                    # Strip dosage form suffix for brand name
                    brand_name = drug_name.rsplit(dosage_form, 1)[0].strip()

                # 1. Condition Match Score (scaled by indication review volume or monograph status)
                cond_review_cnt = int(row["condition_review_count"] or 0)
                if cond_review_cnt > 0:
                    condition_match = float(min(1.0, 0.80 + 0.20 * (min(cond_review_cnt, 50) / 50.0)))
                else:
                    condition_match = 0.90 if indication_type == "Primary" else 0.80

                # 2. Similarity Score
                similarity_score = float(round(symptom_sims[idx], 4))

                # 3. Model-Inferred Sentiment Score with explicit provenance (empirical evidence only)
                sent_info = self.sentiment_model.get_drug_sentiment_info(drug_name, generic_name)
                sentiment_score = sent_info["sentiment_score"]
                sentiment_data_available = sent_info["sentiment_data_available"]
                sentiment_evidence_level = sent_info["sentiment_evidence_level"]
                sentiment_evidence_source = sent_info["sentiment_evidence_source"]

                # 4. Normalized Rating Score (available only if empirical patient ratings exist)
                drug_tot_reviews = int(row["drug_total_reviews"] or 0)
                cond_review_cnt = int(row["condition_review_count"] or 0)
                cond_avg_rating = row["condition_avg_rating"]
                drug_avg_rating = row["drug_avg_rating"]

                brand_review_data_available = (cond_review_cnt > 0 or drug_tot_reviews > 0)
                brand_review_count = cond_review_cnt if cond_review_cnt > 0 else drug_tot_reviews

                if cond_review_cnt > 0 and cond_avg_rating and float(cond_avg_rating) > 0.0:
                    rating_score = float(round(min(10.0, max(0.0, float(cond_avg_rating))) / 10.0, 4))
                    rating_data_available = True
                    display_avg_rating = round(float(cond_avg_rating), 2)
                elif drug_tot_reviews > 0 and drug_avg_rating and float(drug_avg_rating) > 0.0:
                    rating_score = float(round(min(10.0, max(0.0, float(drug_avg_rating))) / 10.0, 4))
                    rating_data_available = True
                    display_avg_rating = round(float(drug_avg_rating), 2)
                else:
                    rating_score = None
                    rating_data_available = False
                    display_avg_rating = None

                # 5. Dynamic Evidence-Aware Weight Renormalization
                # If sentiment or rating is unavailable, renormalize score over available evidence factors
                available_weight_sum = w_cond + w_sim
                weighted_sum = w_cond * condition_match + w_sim * similarity_score

                if sentiment_data_available and sentiment_score is not None:
                    available_weight_sum += w_sent
                    weighted_sum += w_sent * sentiment_score

                if rating_data_available and rating_score is not None:
                    available_weight_sum += w_rat
                    weighted_sum += w_rat * rating_score

                if available_weight_sum > 0:
                    raw_score = float(round(weighted_sum / available_weight_sum, 4))
                else:
                    raw_score = float(round(0.50 * condition_match + 0.50 * similarity_score, 4))

                positive_ratio_val = (
                    round(float(row["positive_sentiment_ratio"]), 4)
                    if brand_review_data_available and row["positive_sentiment_ratio"] is not None
                    else None
                )

                candidates.append({
                    "drug_id": drug_id,
                    "drug_name": drug_name,
                    "brand_name": brand_name,
                    "generic_name": generic_name,
                    "drug_class": drug_class,
                    "composition": composition,
                    "manufacturer": manufacturer,
                    "dosage_form": dosage_form,
                    "pack_size": pack_size,
                    "price_inr": price_inr,
                    "condition": canonical_condition,
                    "evidence_source": evidence_source,
                    "indication_type": indication_type,
                    "raw_score": raw_score,
                    "factors": {
                        "condition_match": round(condition_match, 4),
                        "similarity_score": round(similarity_score, 4),
                        "sentiment_score": sentiment_score,
                        "sentiment_data_available": sentiment_data_available,
                        "sentiment_evidence_level": sentiment_evidence_level,
                        "sentiment_evidence_source": sentiment_evidence_source,
                        "brand_review_data_available": brand_review_data_available,
                        "rating_score": rating_score,
                        "rating_data_available": rating_data_available,
                    },
                    "review_summary": {
                        "positive_ratio": positive_ratio_val,
                        "total_reviews": brand_review_count,
                        "average_rating": display_avg_rating,
                        "condition_review_count": cond_review_cnt,
                    },
                })

            # Sort descending by raw recommendation score
            candidates.sort(key=lambda x: x["raw_score"], reverse=True)
            return candidates

        finally:
            conn.close()

