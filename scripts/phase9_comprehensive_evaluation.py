"""
Comprehensive Phase 9 Testing & Evaluation Script
Executes all empirical measurements, statistical verifications, and safety checks.
"""

import os
import sys
import time
import json
import sqlite3
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.ml.recommendation import ContentRecommender
from app.ml.sentiment import SentimentModel
from app.safety.screening import SafetyScreeningEngine
from app.services.recommendation_service import RecommendationService
from app.ml.preprocessing import clean_review_text

def run_evaluation():
    results = {}
    print("=" * 80)
    print("STARTING PHASE 9 COMPREHENSIVE EVALUATION")
    print("=" * 80)

    # -------------------------------------------------------------
    # 1. DATABASE INTEGRITY
    # -------------------------------------------------------------
    print("\n--- STEP 3: DATABASE INTEGRITY EVALUATION ---")
    db_path = os.path.join(BASE_DIR, "data", "processed", "drug_system.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Integrity Check
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()[0]
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    
    # Table counts
    tables = [
        "drugs", "conditions", "drug_conditions",
        "allergy_crosswalk", "drug_interactions", "contraindications"
    ]
    table_counts = {}
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        table_counts[t] = cursor.fetchone()[0]

    # Check DDI unordered pair constraint (drug_a_id < drug_b_id)
    cursor.execute("SELECT COUNT(*) FROM drug_interactions WHERE drug_a_id >= drug_b_id;")
    invalid_ddi_order = cursor.fetchone()[0]

    # Check duplicate DDI pairs
    cursor.execute("SELECT drug_a_id, drug_b_id, COUNT(*) FROM drug_interactions GROUP BY drug_a_id, drug_b_id HAVING COUNT(*) > 1;")
    duplicate_ddis = cursor.fetchall()

    # Check orphan safety drug references
    cursor.execute("""
        SELECT COUNT(*) FROM allergy_crosswalk WHERE drug_id NOT IN (SELECT drug_id FROM drugs);
    """)
    orphan_allergies = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM drug_interactions 
        WHERE drug_a_id NOT IN (SELECT drug_id FROM drugs) OR drug_b_id NOT IN (SELECT drug_id FROM drugs);
    """)
    orphan_ddis = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM contraindications WHERE drug_id NOT IN (SELECT drug_id FROM drugs);
    """)
    orphan_contraindications = cursor.fetchone()[0]

    results["database"] = {
        "integrity": integrity,
        "foreign_key_violations": len(fk_violations),
        "table_counts": table_counts,
        "invalid_ddi_order_count": invalid_ddi_order,
        "duplicate_ddi_pairs": len(duplicate_ddis),
        "orphan_allergies": orphan_allergies,
        "orphan_ddis": orphan_ddis,
        "orphan_contraindications": orphan_contraindications,
    }
    print(f"Database Integrity: {integrity}")
    print(f"Foreign Key Violations: {len(fk_violations)}")
    print(f"Table Counts: {table_counts}")
    print(f"Invalid DDI Order: {invalid_ddi_order}, Duplicates: {len(duplicate_ddis)}")
    print(f"Orphan Safety Records: Allergies={orphan_allergies}, DDIs={orphan_ddis}, Contra={orphan_contraindications}")
    conn.close()

    # -------------------------------------------------------------
    # 2. DATA QUALITY EVALUATION
    # -------------------------------------------------------------
    print("\n--- STEP 4: DATA QUALITY EVALUATION ---")
    train_path = os.path.join(BASE_DIR, "data", "processed", "drugs_cleaned_train.csv")
    test_path = os.path.join(BASE_DIR, "data", "processed", "drugs_cleaned_test.csv")
    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)
    df_combined = pd.concat([df_train, df_test], ignore_index=True)

    def check_dataset_quality(df, name):
        null_counts = df.isnull().sum().to_dict()
        invalid_ratings = int(df[~df["rating"].between(1, 10)].shape[0])
        empty_reviews = int(df[df["review"].astype(str).str.strip() == ""].shape[0])
        
        # Verify proxy label logic
        expected_labels = df["rating"].apply(lambda r: "Positive" if r >= 7 else ("Neutral" if r >= 5 else "Negative"))
        mismatched_labels = int((df["sentiment_label"] != expected_labels).sum())
        sentiment_dist = {str(k): int(v) for k, v in df["sentiment_label"].value_counts().items()}

        return {
            "name": name,
            "rows": len(df),
            "columns": list(df.columns),
            "null_counts": {k: int(v) for k, v in null_counts.items()},
            "invalid_ratings": invalid_ratings,
            "empty_reviews": empty_reviews,
            "mismatched_sentiment_labels": mismatched_labels,
            "sentiment_distribution": sentiment_dist,
        }

    train_quality = check_dataset_quality(df_train, "train")
    test_quality = check_dataset_quality(df_test, "test")
    results["data_quality"] = {
        "train": train_quality,
        "test": test_quality,
        "total_rows": len(df_train) + len(df_test),
    }
    print(f"Train Rows: {train_quality['rows']}, Nulls: {train_quality['null_counts']}, Sentiment Dist: {train_quality['sentiment_distribution']}")
    print(f"Test Rows: {test_quality['rows']}, Nulls: {test_quality['null_counts']}, Sentiment Dist: {test_quality['sentiment_distribution']}")
    print(f"Label Consistency Checks: Train Mismatches={train_quality['mismatched_sentiment_labels']}, Test Mismatches={test_quality['mismatched_sentiment_labels']}")

    # -------------------------------------------------------------
    # 3. SENTIMENT MODEL INDEPENDENT EVALUATION
    # -------------------------------------------------------------
    print("\n--- STEP 5: SENTIMENT MODEL EVALUATION ---")
    vec_path = os.path.join(BASE_DIR, "models", "sentiment_vectorizer.joblib")
    mod_path = os.path.join(BASE_DIR, "models", "sentiment_model.joblib")
    metrics_json_path = os.path.join(BASE_DIR, "models", "sentiment_metrics.json")

    vectorizer = joblib.load(vec_path)
    model = joblib.load(mod_path)
    with open(metrics_json_path, "r") as f:
        stored_metrics = json.load(f)

    cleaned_test_reviews = df_test["review"].astype(str).apply(clean_review_text)
    X_test = vectorizer.transform(cleaned_test_reviews)
    y_test = df_test["sentiment_label"].values
    y_pred = model.predict(X_test)

    classes = ["Negative", "Neutral", "Positive"]
    acc = float(accuracy_score(y_test, y_pred))
    prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    
    cls_rep = classification_report(y_test, y_pred, target_names=classes, output_dict=True)
    conf_mat = confusion_matrix(y_test, y_pred, labels=classes).tolist()

    computed_metrics = {
        "accuracy": round(acc, 4),
        "precision_macro": round(prec_macro, 4),
        "recall_macro": round(rec_macro, 4),
        "f1_macro": round(f1_macro, 4),
        "f1_weighted": round(f1_weighted, 4),
        "per_class": {
            cls: {
                "precision": round(cls_rep[cls]["precision"], 4),
                "recall": round(cls_rep[cls]["recall"], 4),
                "f1": round(cls_rep[cls]["f1-score"], 4),
                "support": cls_rep[cls]["support"],
            } for cls in classes
        },
        "confusion_matrix": conf_mat,
    }

    results["sentiment_evaluation"] = {
        "computed": computed_metrics,
        "stored": stored_metrics,
        "discrepancy_check": {
            "accuracy_diff": round(abs(computed_metrics["accuracy"] - stored_metrics["sentiment_model"]["accuracy"]), 6),
            "f1_macro_diff": round(abs(computed_metrics["f1_macro"] - stored_metrics["sentiment_model"]["f1_macro"]), 6),
            "f1_weighted_diff": round(abs(computed_metrics["f1_weighted"] - stored_metrics["sentiment_model"]["f1_weighted"]), 6),
        }
    }
    print(f"Independently Calculated Accuracy: {computed_metrics['accuracy']:.4f} (Stored: {stored_metrics['sentiment_model']['accuracy']:.4f})")
    print(f"Independently Calculated F1 Macro: {computed_metrics['f1_macro']:.4f} (Stored: {stored_metrics['sentiment_model']['f1_macro']:.4f})")
    print(f"Independently Calculated F1 Weighted: {computed_metrics['f1_weighted']:.4f} (Stored: {stored_metrics['sentiment_model']['f1_weighted']:.4f})")
    print(f"Confusion Matrix (labels={classes}): {conf_mat}")

    # -------------------------------------------------------------
    # 4. SENTIMENT ROBUSTNESS TESTING
    # -------------------------------------------------------------
    print("\n--- STEP 6: SENTIMENT ROBUSTNESS TESTING ---")
    sent_model = SentimentModel()
    robustness_cases = [
        ("Clearly positive", "This medication worked wonders! My symptoms disappeared in two days with zero side effects."),
        ("Clearly negative", "Horrible experience. Caused severe nausea, extreme vomiting, and did not relieve any pain."),
        ("Neutral/Mixed", "The medicine was okay. It reduced the fever slightly but gave me a mild headache."),
        ("Negation", "I did not experience any improvement at all, and it is not worth taking."),
        ("Short review", "Great drug!"),
        ("Longer review", "I have been taking this prescription for six months after being diagnosed with chronic hypertension. Overall my blood pressure stabilized from 150/95 down to 120/80. I experienced mild dry cough during the first two weeks, but it subsided completely."),
        ("Punctuation-heavy", "AMAZING!!! Best treatment EVER :) 10/10 !!!"),
        ("Empty/Whitespace", "   \n\t  "),
        ("Unusual characters", "Taking 500mg @ bedtime... feeling #better :) & 100% fine!"),
    ]

    robustness_results = []
    for case_name, text in robustness_cases:
        pred = sent_model.predict(text)
        res_entry = {
            "case": case_name,
            "text": text,
            "predicted_sentiment": pred["predicted_sentiment"],
            "polarity_score": pred["polarity_score"],
            "confidence": pred["confidence"],
            "top_keywords": pred["top_keywords"],
            "valid": pred["predicted_sentiment"] in classes and 0.0 <= pred["polarity_score"] <= 1.0 and 0.0 <= pred["confidence"] <= 1.0
        }
        robustness_results.append(res_entry)
        print(f"[{'PASS' if res_entry['valid'] else 'FAIL'}] {case_name}: '{text[:30]}...' -> {pred['predicted_sentiment']} (polarity={pred['polarity_score']:.2f}, conf={pred['confidence']:.2f})")
    results["sentiment_robustness"] = robustness_results

    # -------------------------------------------------------------
    # 5. RECOMMENDATION ENGINE EVALUATION
    # -------------------------------------------------------------
    print("\n--- STEP 7: RECOMMENDATION ENGINE EVALUATION ---")
    recommender = ContentRecommender()
    
    rec_tests = [
        ("Known condition (default weights)", "Type 2 Diabetes", ["fatigue", "elevated blood sugar"], None),
        ("Known condition (no symptoms)", "Hypertension", [], None),
        ("Known condition (custom weights)", "Depression", ["low mood", "insomnia"], {"condition_match": 0.5, "similarity": 0.2, "sentiment": 0.2, "rating": 0.1}),
        ("Unknown condition", "NonExistentConditionX", [], None),
    ]

    rec_results = []
    for test_name, cond, symptoms, weights in rec_tests:
        candidates = recommender.get_candidate_drugs(
            condition=cond,
            symptoms=symptoms,
            weights=weights
        )
        valid_candidates = True
        for c in candidates:
            factors = c["factors"]
            has_all_factors = all(k in factors for k in ["condition_match", "similarity_score", "sentiment_score", "rating_score"])
            no_safety_in_factors = "safety_compatibility" not in factors
            score_bounded = 0.0 <= c["raw_score"] <= 1.0
            if not (has_all_factors and no_safety_in_factors and score_bounded):
                valid_candidates = False
                break
        
        entry = {
            "test": test_name,
            "condition": cond,
            "candidate_count": len(candidates),
            "top_drug": candidates[0]["drug_name"] if candidates else None,
            "top_score": candidates[0]["raw_score"] if candidates else None,
            "valid": valid_candidates
        }
        rec_results.append(entry)
        print(f"[{'PASS' if valid_candidates else 'FAIL'}] {test_name}: candidates={len(candidates)}, top={entry['top_drug']} (score={entry['top_score']})")

    # Verify determinism: run identical query twice
    run1 = recommender.get_candidate_drugs("Depression", ["fatigue"])
    run2 = recommender.get_candidate_drugs("Depression", ["fatigue"])
    determinism_pass = [c1["drug_id"] for c1 in run1] == [c2["drug_id"] for c2 in run2]
    print(f"Determinism Check: {'PASS' if determinism_pass else 'FAIL'}")
    results["recommendation_engine"] = {
        "tests": rec_results,
        "determinism": determinism_pass
    }

    # -------------------------------------------------------------
    # 6. DRUG-LEVEL SENTIMENT AGGREGATION VERIFICATION
    # -------------------------------------------------------------
    print("\n--- STEP 8: DRUG-LEVEL SENTIMENT AGGREGATION ---")
    drug_sentiment_scores = joblib.load(os.path.join(BASE_DIR, "models", "drug_sentiment_scores.joblib"))
    
    sample_drug_names = ["Metformin", "Lisinopril", "Sertraline", "Levothyroxine", "Amlodipine"]
    agg_checks = []
    for d_name in sample_drug_names:
        drug_revs = df_combined[df_combined["drugName"] == d_name]["review"].dropna()
        if len(drug_revs) > 0:
            cleaned_revs = drug_revs.astype(str).apply(clean_review_text)
            X_revs = vectorizer.transform(cleaned_revs)
            probs = model.predict_proba(X_revs)[:, 2] # index 2 is Positive
            mean_pos = float(np.mean(probs))
            stored_val = float(drug_sentiment_scores.get(d_name, 0.5))
            diff = abs(mean_pos - stored_val)
            match = diff < 0.001 # floating tolerance
            agg_checks.append({
                "drug_name": d_name,
                "review_count": len(drug_revs),
                "recalculated_mean": round(mean_pos, 4),
                "stored_score": round(stored_val, 4),
                "difference": round(diff, 6),
                "match": match
            })
            print(f"Drug '{d_name}': Recalculated={mean_pos:.4f}, Stored={stored_val:.4f}, Diff={diff:.6f} -> {'PASS' if match else 'FAIL'}")
    results["drug_sentiment_aggregation"] = agg_checks

    # -------------------------------------------------------------
    # 7. SAFETY ENGINE EVALUATION
    # -------------------------------------------------------------
    print("\n--- STEP 9: SAFETY ENGINE EVALUATION ---")
    safety_engine = SafetyScreeningEngine()
    
    # A. No matching rule (Amlodipine, no meds/allergies)
    eval_a = safety_engine.screen_candidate(candidate="Amlodipine", age=45, condition="Hypertension", allergies=[], current_medications=[])
    
    # B. Allergy conflict (Lisinopril with ACE Inhibitors allergy)
    eval_b = safety_engine.screen_candidate(candidate="Lisinopril", age=50, condition="Hypertension", allergies=["ACE Inhibitors"], current_medications=[])
    
    # C. Moderate DDI (Lisinopril + Ibuprofen)
    eval_c = safety_engine.screen_candidate(candidate="Lisinopril", age=50, condition="Hypertension", allergies=[], current_medications=["Ibuprofen"])
    
    # D. Severe DDI (Aspirin + Warfarin)
    eval_d = safety_engine.screen_candidate(candidate="Aspirin", age=50, condition="Pain", allergies=[], current_medications=["Warfarin"])
    
    # E. Age Contraindication (Aspirin for child age 12)
    eval_e = safety_engine.screen_candidate(candidate="Aspirin", age=12, condition="Pain", allergies=[], current_medications=[])

    # F. Multiple simultaneous conflicts (Lisinopril with ACE Inhibitors allergy + Ibuprofen DDI)
    eval_f = safety_engine.screen_candidate(candidate="Lisinopril", age=50, condition="Hypertension", allergies=["ACE Inhibitors"], current_medications=["Ibuprofen"])
    
    # G. Unknown allergy & unknown medication
    eval_g = safety_engine.screen_candidate(candidate="Amlodipine", age=45, condition="Hypertension", allergies=["UnknownAllergenX"], current_medications=["UnknownDrugY"])

    safety_tests = [
        ("A: No matching rule", eval_a["safety_status"] == "NO_KNOWN_CONFLICT", eval_a["safety_status"]),
        ("B: Allergy conflict", eval_b["safety_status"] == "FILTERED_SAFETY_CONFLICT", eval_b["safety_status"]),
        ("C: Moderate DDI", eval_c["safety_status"] == "WARNING", eval_c["safety_status"]),
        ("D: Severe DDI", eval_d["safety_status"] == "FILTERED_SAFETY_CONFLICT", eval_d["safety_status"]),
        ("E: Age Contraindication", eval_e["safety_status"] == "FILTERED_SAFETY_CONFLICT", eval_e["safety_status"]),
        ("F: Multiple conflicts priority", eval_f["safety_status"] == "FILTERED_SAFETY_CONFLICT", eval_f["safety_status"]),
        ("G: Unknown allergy/med no fabrication", eval_g["safety_status"] == "NO_KNOWN_CONFLICT", eval_g["safety_status"]),
    ]

    for name, passed, status in safety_tests:
        print(f"[{'PASS' if passed else 'FAIL'}] {name} -> Status: {status}")
    results["safety_engine"] = {name: {"status": status, "pass": passed} for name, passed, status in safety_tests}

    # -------------------------------------------------------------
    # 8. SAFETY DATA TRACEABILITY
    # -------------------------------------------------------------
    print("\n--- STEP 10: SAFETY DATA TRACEABILITY ---")
    rules_json_path = os.path.join(BASE_DIR, "data", "safety", "verified_safety_rules.json")
    with open(rules_json_path, "r") as f:
        safety_rules_data = json.load(f)

    allergy_rules = safety_rules_data.get("allergies", [])
    ddi_rules = safety_rules_data.get("interactions", [])
    contra_rules = safety_rules_data.get("contraindications", [])

    def check_sources(rules_list):
        missing = 0
        for r in rules_list:
            if not (r.get("source") or r.get("evidence_source") or r.get("clinical_reason")):
                missing += 1
        return len(rules_list), missing

    a_len, a_mis = check_sources(allergy_rules)
    d_len, d_mis = check_sources(ddi_rules)
    c_len, c_mis = check_sources(contra_rules)

    print(f"Allergy rules: {a_len} rules (missing source: {a_mis})")
    print(f"DDI rules: {d_len} rules (missing source: {d_mis})")
    print(f"Contraindication rules: {c_len} rules (missing source: {c_mis})")
    results["safety_traceability"] = {
        "allergy_count": a_len,
        "ddi_count": d_len,
        "contraindication_count": c_len,
        "all_rules_traceable": (a_mis == 0 and d_mis == 0 and c_mis == 0)
    }

    # -------------------------------------------------------------
    # 9. API TESTING & CONTRACT VERIFICATION
    # -------------------------------------------------------------
    print("\n--- STEP 11 & 12: API TESTING & CONTRACT VERIFICATION ---")
    client = TestClient(app)
    
    api_tests = []
    # 1. Health
    res = client.get("/api/v1/health")
    api_tests.append(("GET /api/v1/health", res.status_code == 200, res.status_code))
    
    # 2. Conditions
    res = client.get("/api/v1/conditions")
    api_tests.append(("GET /api/v1/conditions", res.status_code == 200 and res.json()["total_conditions"] == 836, res.status_code))

    # 3. Allergies
    res = client.get("/api/v1/allergies")
    api_tests.append(("GET /api/v1/allergies", res.status_code == 200 and len(res.json()["allergen_classes"]) == 14, res.status_code))

    # 4. Drugs list
    res = client.get("/api/v1/drugs?limit=10")
    api_tests.append(("GET /api/v1/drugs", res.status_code == 200 and res.json()["total_drugs"] == 3654, res.status_code))

    # 5. Drug Detail
    res = client.get("/api/v1/drugs/1")
    api_tests.append(("GET /api/v1/drugs/1", res.status_code == 200 and "drug_id" in res.json(), res.status_code))

    # 6. Model Metrics
    res = client.get("/api/v1/model/metrics")
    api_tests.append(("GET /api/v1/model/metrics", res.status_code == 200 and res.json()["model_evaluated"] is True, res.status_code))

    # 7. Sentiment Analyze
    res = client.post("/api/v1/sentiment/analyze", json={"text": "Very good relief."})
    api_tests.append(("POST /api/v1/sentiment/analyze", res.status_code == 200 and res.json()["predicted_sentiment"] == "Positive", res.status_code))

    # 8. Recommend (Valid)
    rec_payload = {
        "age": 35,
        "condition": "Depression",
        "symptoms": ["fatigue"],
        "allergies": ["Penicillin"],
        "current_medications": ["Warfarin"]
    }
    res = client.post("/api/v1/recommend", json=rec_payload)
    rec_json = res.json()
    contract_ok = True
    if res.status_code == 200:
        if "disclaimer" not in rec_json: contract_ok = False
        for r in rec_json.get("recommended_drugs", []):
            if "safety_compatibility" in r.get("factors", {}): contract_ok = False
            if "safety_status" not in r: contract_ok = False
        for f_drug in rec_json.get("filtered_drugs", []):
            if "clinical_reason" not in f_drug or "severity" not in f_drug: contract_ok = False
    else:
        contract_ok = False
    api_tests.append(("POST /api/v1/recommend (Contract Check)", res.status_code == 200 and contract_ok, res.status_code))

    # Invalid input tests
    res_inv_age = client.post("/api/v1/recommend", json={"age": -5, "condition": "Depression"})
    api_tests.append(("POST /api/v1/recommend (Invalid Age)", res_inv_age.status_code in [400, 422], res_inv_age.status_code))

    res_non_drug = client.get("/api/v1/drugs/999999")
    api_tests.append(("GET /api/v1/drugs/999999 (Nonexistent ID)", res_non_drug.status_code == 404, res_non_drug.status_code))

    for name, ok, code in api_tests:
        print(f"[{'PASS' if ok else 'FAIL'}] {name} -> Code: {code}")
    results["api_tests"] = {name: {"code": code, "pass": ok} for name, ok, code in api_tests}

    # -------------------------------------------------------------
    # 10. LATENCY & PERFORMANCE MEASUREMENTS (20 repetitions)
    # -------------------------------------------------------------
    print("\n--- STEP 15: LATENCY PERFORMANCE MEASUREMENTS (20 Repetitions) ---")
    endpoints_to_measure = [
        ("GET /api/v1/health", lambda: client.get("/api/v1/health")),
        ("POST /api/v1/recommend", lambda: client.post("/api/v1/recommend", json={"age": 45, "condition": "Type 2 Diabetes", "symptoms": ["fatigue"], "allergies": [], "current_medications": []})),
        ("POST /api/v1/sentiment/analyze", lambda: client.post("/api/v1/sentiment/analyze", json={"text": "This drug gave me great pain relief without any side effects."})),
        ("GET /api/v1/drugs (limit=10)", lambda: client.get("/api/v1/drugs?limit=10")),
        ("GET /api/v1/drugs/1", lambda: client.get("/api/v1/drugs/1")),
    ]

    perf_results = {}
    for ep_name, call_fn in endpoints_to_measure:
        latencies = []
        for _ in range(20):
            t0 = time.perf_counter()
            call_fn()
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)
        
        avg_ms = float(np.mean(latencies))
        min_ms = float(np.min(latencies))
        max_ms = float(np.max(latencies))
        perf_results[ep_name] = {
            "repetitions": 20,
            "avg_ms": round(avg_ms, 2),
            "min_ms": round(min_ms, 2),
            "max_ms": round(max_ms, 2),
        }
        print(f"Latency {ep_name}: Avg={avg_ms:.2f}ms (Min={min_ms:.2f}ms, Max={max_ms:.2f}ms)")
    results["performance"] = perf_results

    # -------------------------------------------------------------
    # 11. SECURITY & INPUT ROBUSTNESS CHECKS
    # -------------------------------------------------------------
    print("\n--- STEP 16: SECURITY & INPUT ROBUSTNESS CHECKS ---")
    sec_tests = []
    
    # SQL Injection in Condition
    sql_payload = {"age": 30, "condition": "Depression' OR '1'='1", "symptoms": [], "allergies": [], "current_medications": []}
    res_sql = client.post("/api/v1/recommend", json=sql_payload)
    sec_tests.append(("SQL Injection in condition", res_sql.status_code == 200, "Safely handled (parameterized)"))

    # Oversized Sentiment Text (140KB)
    large_text = "This medication is helpful. " * 5000
    res_large = client.post("/api/v1/sentiment/analyze", json={"text": large_text})
    sec_tests.append(("Oversized Sentiment Text (140KB)", res_large.status_code == 200, "Successfully analyzed without crash"))

    # Malformed JSON
    res_malformed = client.post("/api/v1/recommend", content="not-a-json", headers={"Content-Type": "application/json"})
    sec_tests.append(("Malformed JSON payload", res_malformed.status_code == 422, "422 Unprocessable Entity"))

    for name, passed, notes in sec_tests:
        print(f"[{'PASS' if passed else 'FAIL'}] {name} -> {notes}")
    results["security_robustness"] = sec_tests

    # Save output results
    output_path = os.path.join(BASE_DIR, "docs", "phase9_evaluation_data.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nEvaluation data written to: {output_path}")
    print("=" * 80)
    print("PHASE 9 EVALUATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_evaluation()
