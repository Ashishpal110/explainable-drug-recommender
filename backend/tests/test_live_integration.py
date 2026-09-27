"""
Live integration verification script for FastAPI recommendation backend.
"""

import json
from fastapi.testclient import TestClient
from app.main import app


def run_integration_tests():
    client = TestClient(app)
    print("--- 1. Testing Health Endpoint ---")
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health = resp.json()
    print("Health Status:", json.dumps(health, indent=2))
    assert health["status"] == "healthy"
    assert health["models_loaded"] is True

    print("\n--- 2. Testing Recommendation with Allergy Conflict & DDI ---")
    payload = {
        "age": 52,
        "condition": "High Blood Pressure",
        "symptoms": ["headache", "fatigue"],
        "allergies": ["ACE Inhibitors"],
        "current_medications": ["Potassium Chloride"],
        "weights": {
            "condition_match": 0.40,
            "similarity": 0.30,
            "sentiment": 0.20,
            "rating": 0.10,
        },
    }
    resp = client.post("/api/v1/recommend", json=payload)
    assert resp.status_code == 200, f"Recommendation failed: {resp.text}"
    data = resp.json()

    print(f"Condition: {data['patient_summary']['condition']}")
    print(f"Recommended candidates count: {len(data['recommended_drugs'])}")
    print(f"Filtered unsafe candidates count: {len(data['filtered_drugs'])}")
    print(f"Disclaimer present: {'NO_KNOWN_CONFLICT' in data['disclaimer']}")

    # Verify Lisinopril is in filtered_drugs due to ACE Inhibitor allergy
    filtered_names = [f["drug_name"] for f in data["filtered_drugs"]]
    print("Filtered drug names:", filtered_names)
    assert "Lisinopril" in filtered_names, "Lisinopril must be filtered due to ACE Inhibitor allergy!"

    lisinopril_filter = next(f for f in data["filtered_drugs"] if f["drug_name"] == "Lisinopril")
    print("Lisinopril Filter Audit:", json.dumps(lisinopril_filter, indent=2))
    assert lisinopril_filter["safety_status"] == "FILTERED_SAFETY_CONFLICT"
    assert "ALLERGY_CONFLICT" in lisinopril_filter["exact_rule_triggered"]

    # Verify recommended candidates
    if len(data["recommended_drugs"]) > 0:
        first_rec = data["recommended_drugs"][0]
        print("\nTop Recommended Drug:", json.dumps(first_rec, indent=2))
        assert first_rec["safety_status"] in ("NO_KNOWN_CONFLICT", "WARNING")
        assert "condition_match" in first_rec["factors"]
        assert "similarity_score" in first_rec["factors"]
        assert "sentiment_score" in first_rec["factors"]
        assert "rating_score" in first_rec["factors"]
        # Ensure safety_compatibility is NOT in factors
        assert "safety_compatibility" not in first_rec["factors"], "safety_compatibility MUST NOT be in factors!"

    print("\n--- 3. Testing Pediatric Contraindication (<18 with contraindicated drug) ---")
    pedia_payload = {
        "age": 10,
        "condition": "Depression",
        "symptoms": ["sadness"],
        "allergies": [],
        "current_medications": [],
    }
    resp = client.post("/api/v1/recommend", json=pedia_payload)
    assert resp.status_code == 200
    pedia_data = resp.json()
    pedia_filtered = [f["drug_name"] for f in pedia_data["filtered_drugs"]]
    print("Pediatric (<18) Filtered Drugs for Depression:", pedia_filtered)

    print("\n--- 4. Testing Unknown Indication Query ---")
    unknown_payload = {
        "age": 30,
        "condition": "NonExistentExtraterrestrialCondition12345",
        "symptoms": [],
        "allergies": [],
        "current_medications": [],
    }
    resp = client.post("/api/v1/recommend", json=unknown_payload)
    assert resp.status_code == 200
    unknown_data = resp.json()
    assert len(unknown_data["recommended_drugs"]) == 0
    assert len(unknown_data["filtered_drugs"]) == 0
    print("Unknown condition returned empty candidate list gracefully without crash.")

    print("\n--- 5. Testing Invalid Payload (Negative Age) ---")
    invalid_payload = {
        "age": -5,
        "condition": "High Blood Pressure",
        "symptoms": [],
        "allergies": [],
        "current_medications": [],
    }
    resp = client.post("/api/v1/recommend", json=invalid_payload)
    assert resp.status_code == 422, f"Expected 422 for negative age, got {resp.status_code}"
    print("Schema validation rejected negative age with 422 Unprocessable Entity as expected.")

    print("\nALL LIVE INTEGRATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_integration_tests()
