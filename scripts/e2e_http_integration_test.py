"""
E2E HTTP network test script against the running FastAPI backend server on http://127.0.0.1:8000.
"""

import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"


def make_request(method, path, body=None, headers=None):
    url = f"{BASE_URL}{path}"
    headers = headers or {}
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"
    
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            res_headers = dict(response.headers)
            return response.status, json.loads(res_body) if res_body else {}, res_headers
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw": err_body}
        return e.code, err_json, dict(e.headers)


def run_tests():
    print("=" * 70)
    print("PHASE 8 — FULL SYSTEM INTEGRATION HTTP TESTS")
    print("=" * 70)

    # 1. Health check
    status, data, _ = make_request("GET", "/health")
    assert status == 200, f"Health check failed: {status}"
    print(f"[PASS] GET /health -> Status: {status}, db: {data.get('database')}, models_loaded: {data.get('models_loaded')}")

    # 2. CORS Verification
    cors_headers = {"Origin": "http://localhost:5173"}
    status, _, headers = make_request("GET", "/health", headers=cors_headers)
    allow_origin = headers.get("access-control-allow-origin") or headers.get("Access-Control-Allow-Origin")
    print(f"[PASS] CORS check -> Origin: http://localhost:5173, Access-Control-Allow-Origin: {allow_origin}")
    assert allow_origin in ("http://localhost:5173", "*"), f"CORS failed for http://localhost:5173: {allow_origin}"

    # 3. Conditions Catalog
    status, data, _ = make_request("GET", "/conditions")
    assert status == 200
    assert data["total_conditions"] == 836
    print(f"[PASS] GET /conditions -> Total conditions: {data['total_conditions']}")

    # 4. Allergies Catalog
    status, data, _ = make_request("GET", "/allergies")
    assert status == 200
    assert len(data["allergen_classes"]) == 14
    print(f"[PASS] GET /allergies -> Total allergen classes: {len(data['allergen_classes'])} ({data['allergen_classes'][:4]}...)")

    # 5. Drugs Catalog & Detail
    status, data, _ = make_request("GET", "/drugs?limit=5")
    assert status == 200
    assert data["total_drugs"] == 3654
    first_drug_id = data["drugs"][0]["drug_id"]
    print(f"[PASS] GET /drugs -> Total drugs: {data['total_drugs']}, first drug: {data['drugs'][0]['name']}")

    status, drug_detail, _ = make_request("GET", f"/drugs/{first_drug_id}")
    assert status == 200
    print(f"[PASS] GET /drugs/{first_drug_id} -> {drug_detail['name']}, indications: {len(drug_detail['indicated_conditions'])}, contraindications: {len(drug_detail['contraindications'])}")

    # 6. Model Metrics
    status, data, _ = make_request("GET", "/model/metrics")
    assert status == 200
    assert data["model_evaluated"] is True
    assert data["sentiment_model"]["accuracy"] == 0.8023
    print(f"[PASS] GET /model/metrics -> Accuracy: {data['sentiment_model']['accuracy']}, F1-Macro: {data['sentiment_model']['f1_macro']}")

    # 7. Sentiment Analysis (Step 6)
    rev_text = "Very effective medication and I experienced very few side effects."
    status, data, _ = make_request("POST", "/sentiment/analyze", {"text": rev_text})
    assert status == 200
    assert data["predicted_sentiment"] == "Positive"
    assert data["polarity_score"] >= 0.50
    print(f"[PASS] POST /sentiment/analyze -> Text: '{rev_text}' => Class: {data['predicted_sentiment']}, Polarity: {data['polarity_score']}, Confidence: {data['confidence']}, Keywords: {data['top_keywords']}")

    # 8. Step 5 — Safety Integration Tests (TEST A, B, C)
    print("\n--- SAFETY INTEGRATION SCENARIOS ---")
    
    # TEST A: No Known Conflict
    payload_a = {
        "age": 45,
        "condition": "High Blood Pressure",
        "symptoms": ["headache", "fatigue"],
        "allergies": [],
        "current_medications": []
    }
    status, res_a, _ = make_request("POST", "/recommend", payload_a)
    assert status == 200
    assert len(res_a["recommended_drugs"]) > 0
    top_a = res_a["recommended_drugs"][0]
    assert top_a["safety_status"] == "NO_KNOWN_CONFLICT"
    print(f"[PASS TEST A] No Known Conflict: {top_a['drug_name']} -> safety_status: {top_a['safety_status']}")

    # TEST B: Moderate DDI Warning
    payload_b = {
        "age": 60,
        "condition": "High Blood Pressure",
        "symptoms": [],
        "allergies": [],
        "current_medications": ["Simvastatin"]
    }
    status, res_b, _ = make_request("POST", "/recommend", payload_b)
    assert status == 200
    amlodipine_cand = next((r for r in res_b["recommended_drugs"] if r["drug_name"] == "Amlodipine"), None)
    assert amlodipine_cand is not None
    assert amlodipine_cand["safety_status"] == "WARNING"
    print(f"[PASS TEST B] Moderate DDI: Amlodipine -> safety_status: {amlodipine_cand['safety_status']}, ddi_warnings: {len(amlodipine_cand['safety_details']['ddi_warnings'])}")

    # TEST C: Filtered Safety Conflict (Allergy & Severe DDI)
    payload_c = {
        "age": 52,
        "condition": "High Blood Pressure",
        "symptoms": [],
        "allergies": ["ACE Inhibitors"],
        "current_medications": ["Potassium Chloride"]
    }
    status, res_c, _ = make_request("POST", "/recommend", payload_c)
    assert status == 200
    filtered_names = [f["drug_name"] for f in res_c["filtered_drugs"]]
    assert "Lisinopril" in filtered_names
    lisinopril_filter = next(f for f in res_c["filtered_drugs"] if f["drug_name"] == "Lisinopril")
    assert lisinopril_filter["safety_status"] == "FILTERED_SAFETY_CONFLICT"
    print(f"[PASS TEST C] Severe Conflict: Lisinopril -> safety_status: {lisinopril_filter['safety_status']}, rule: {lisinopril_filter['exact_rule_triggered']}, severity: {lisinopril_filter['severity']}")

    # 9. Step 10 — Error and Edge Case Testing
    print("\n--- EDGE CASE & ROBUSTNESS TESTS ---")
    
    # 1. Empty sentiment text
    status, data, _ = make_request("POST", "/sentiment/analyze", {"text": ""})
    assert status == 200
    assert data["predicted_sentiment"] == "Neutral"
    print("[PASS Edge 1] Empty sentiment text handled gracefully (Neutral, polarity: 0.5)")

    # 2. Unknown medical condition
    status, data, _ = make_request("POST", "/recommend", {"age": 30, "condition": "AlienDisease999", "symptoms": [], "allergies": [], "current_medications": []})
    assert status == 200
    assert len(data["recommended_drugs"]) == 0 and len(data["filtered_drugs"]) == 0
    print("[PASS Edge 2] Unknown medical condition returns empty lists gracefully")

    # 3. Unknown current medication
    status, data, _ = make_request("POST", "/recommend", {"age": 40, "condition": "Pain", "symptoms": [], "allergies": [], "current_medications": ["FictionalDrug999"]})
    assert status == 200
    assert len(data["recommended_drugs"]) > 0
    print("[PASS Edge 3] Unknown current medication handled without false alarms")

    # 4. Unknown allergy class
    status, data, _ = make_request("POST", "/recommend", {"age": 40, "condition": "Pain", "symptoms": [], "allergies": ["UnknownAllergyClassXYZ"], "current_medications": []})
    assert status == 200
    assert len(data["recommended_drugs"]) > 0
    print("[PASS Edge 4] Unknown allergy class handled without false alarms")

    # 5. No current medications
    status, data, _ = make_request("POST", "/recommend", {"age": 40, "condition": "Pain", "symptoms": [], "allergies": [], "current_medications": []})
    assert status == 200
    print("[PASS Edge 5] No current medications handled normally")

    # 6. Invalid patient age (<0 or >125)
    status, data, _ = make_request("POST", "/recommend", {"age": -5, "condition": "Pain", "symptoms": [], "allergies": [], "current_medications": []})
    assert status == 422
    print(f"[PASS Edge 6] Invalid patient age rejected with HTTP 422: {data.get('detail', [{}])[0].get('msg')}")

    # 7. Empty symptoms, allergies, medication lists
    status, data, _ = make_request("POST", "/recommend", {"age": 50, "condition": "High Blood Pressure", "symptoms": [], "allergies": [], "current_medications": []})
    assert status == 200
    print("[PASS Edge 7] Empty optional lists correctly handled as clean defaults")

    print("\n" + "=" * 70)
    print("ALL E2E HTTP INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
