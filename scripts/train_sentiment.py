"""
Offline training and evaluation script for the TF-IDF + Logistic Regression sentiment model.
"""

import time
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train_and_evaluate():
    print("=" * 60)
    print("PHASE 3: TRAINING NLP SENTIMENT MODEL & EVALUATING ON TEST SPLIT")
    print("=" * 60)

    train_path = PROCESSED_DIR / "drugs_cleaned_train.csv"
    test_path = PROCESSED_DIR / "drugs_cleaned_test.csv"
    combined_path = PROCESSED_DIR / "drugs_cleaned_combined.csv"

    print("Loading train and test datasets...")
    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)

    X_train_text = df_train["review"].fillna("").values
    y_train = df_train["sentiment_label"].values

    X_test_text = df_test["review"].fillna("").values
    y_test = df_test["sentiment_label"].values

    classes = ["Negative", "Neutral", "Positive"]
    print(f"Train samples: {len(X_train_text):,}")
    print(f"Test samples:  {len(X_test_text):,}")

    # 1. Feature Extraction (TF-IDF)
    print("\nFitting TF-IDF Vectorizer (ngram_range=(1, 2), max_features=35,000, sublinear_tf=True)...")
    t0_vec = time.time()
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=35000,
        sublinear_tf=True,
        min_df=3,
        strip_accents="unicode",
    )
    X_train_tfidf = vectorizer.fit_transform(X_train_text)
    t_vec = time.time() - t0_vec
    print(f"Vectorization completed in {t_vec:.2f}s. Vocab size: {len(vectorizer.vocabulary_):,}")

    # 2. Classifier Training
    print("\nTraining Logistic Regression classifier (C=1.0, solver='lbfgs', max_iter=1000)...")
    t0_train = time.time()
    classifier = LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight="balanced",
        solver="lbfgs",
        random_state=42,
        n_jobs=-1,
    )
    classifier.fit(X_train_tfidf, y_train)
    t_train = time.time() - t0_train
    print(f"Training completed in {t_train:.2f}s.")

    # 3. Test Evaluation
    print("\nEvaluating on holdout test set...")
    t0_eval = time.time()
    X_test_tfidf = vectorizer.transform(X_test_text)
    y_pred = classifier.predict(X_test_tfidf)
    y_proba = classifier.predict_proba(X_test_tfidf)
    t_eval = time.time() - t0_eval

    acc = float(accuracy_score(y_test, y_pred))
    p_macro = float(precision_score(y_test, y_pred, average="macro", labels=classes))
    r_macro = float(recall_score(y_test, y_pred, average="macro", labels=classes))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", labels=classes))

    p_weighted = float(precision_score(y_test, y_pred, average="weighted", labels=classes))
    r_weighted = float(recall_score(y_test, y_pred, average="weighted", labels=classes))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted", labels=classes))

    cm = confusion_matrix(y_test, y_pred, labels=classes).tolist()
    clf_report_dict = classification_report(y_test, y_pred, labels=classes, output_dict=True)
    clf_report_text = classification_report(y_test, y_pred, labels=classes)

    print("\n" + "=" * 60)
    print("ACTUAL OBSERVED TEST EVALUATION RESULTS")
    print("=" * 60)
    print(f"Accuracy:          {acc:.4f} ({acc*100:.2f}%)")
    print(f"Macro Precision:   {p_macro:.4f}")
    print(f"Macro Recall:      {r_macro:.4f}")
    print(f"Macro F1-Score:    {f1_macro:.4f}")
    print(f"Weighted F1-Score: {f1_weighted:.4f}")
    print("\nConfusion Matrix (Rows: True, Cols: Pred):")
    print(f"Labels: {classes}")
    for row_name, row in zip(classes, cm):
        print(f"  {row_name:10s}: {row}")
    print("\nClassification Report:\n", clf_report_text)
    print("=" * 60)

    # 4. Serialize Model Artifacts
    vec_path = MODELS_DIR / "sentiment_vectorizer.joblib"
    model_path = MODELS_DIR / "sentiment_model.joblib"
    metrics_path = MODELS_DIR / "sentiment_metrics.json"

    print(f"Saving artifacts to {MODELS_DIR}...")
    joblib.dump(vectorizer, vec_path)
    joblib.dump(classifier, model_path)

    metrics_payload = {
        "model_evaluated": True,
        "sentiment_model": {
            "model_name": "TF-IDF + Logistic Regression",
            "classifier": "LogisticRegression(C=1.0, solver='lbfgs', class_weight='balanced')",
            "vectorizer": "TfidfVectorizer(ngram_range=(1, 2), max_features=35000, sublinear_tf=True)",
            "supervision_method": "Rating-derived proxy labels (Positive >= 7, Neutral 5-6, Negative <= 4)",
            "evaluation_dataset_split": "Drugs.com Holdout Test Split (drugs_cleaned_test.csv)",
            "test_samples": int(len(X_test_text)),
            "train_samples": int(len(X_train_text)),
            "accuracy": round(acc, 4),
            "precision_macro": round(p_macro, 4),
            "recall_macro": round(r_macro, 4),
            "f1_macro": round(f1_macro, 4),
            "precision_weighted": round(p_weighted, 4),
            "recall_weighted": round(r_weighted, 4),
            "f1_weighted": round(f1_weighted, 4),
            "classes": classes,
            "confusion_matrix": {
                "labels": classes,
                "matrix": cm,
            },
            "per_class_metrics": {
                c: {
                    "precision": round(clf_report_dict[c]["precision"], 4),
                    "recall": round(clf_report_dict[c]["recall"], 4),
                    "f1-score": round(clf_report_dict[c]["f1-score"], 4),
                    "support": int(clf_report_dict[c]["support"]),
                }
                for c in classes
            },
            "training_time_seconds": round(t_train, 2),
            "vectorization_time_seconds": round(t_vec, 2),
            "evaluation_time_seconds": round(t_eval, 2),
        },
        "recommendation_engine": {
            "algorithm": "Content-Based Cosine Similarity + Review Sentiment Weighting",
            "feature_representation": "TF-IDF Vector Space (Condition, Profile, Review Aspects)",
        },
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"Saved metrics to {metrics_path.name}")

    # 5. Compute Model-Inferred Drug-Level Sentiment Scores
    print("\nComputing model-inferred drug-level sentiment scores across all reviews...")
    df_combined = pd.read_csv(combined_path)
    X_all_tfidf = vectorizer.transform(df_combined["review"].fillna("").values)

    # Class index for 'Positive'
    pos_idx = list(classifier.classes_).index("Positive")
    pos_probs = classifier.predict_proba(X_all_tfidf)[:, pos_idx]
    df_combined["model_positive_prob"] = pos_probs

    # Aggregate mean positive probability per drug
    drug_sentiment_agg = (
        df_combined.groupby("drugName")["model_positive_prob"]
        .mean()
        .round(4)
        .to_dict()
    )

    drug_scores_path = MODELS_DIR / "drug_sentiment_scores.joblib"
    joblib.dump(drug_sentiment_agg, drug_scores_path)
    print(f"Saved model-inferred sentiment scores for {len(drug_sentiment_agg):,} drugs to {drug_scores_path.name}")
    print("\nPhase 3 Model Training & Evaluation Complete.")


if __name__ == "__main__":
    train_and_evaluate()
