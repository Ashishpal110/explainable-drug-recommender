"""
Integration tests for the Recommendation API, Safety Filtering, and Service Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import PatientProfileRequest


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def rec_service():
    return RecommendationService()


def test_recommendation_service_with_allergy_filtering(rec_service):
    """
    Test that a patient with Hypertension and ACE Inhibitor allergy has ACE inhibitor formulations filtered out to filtered_drugs.
    """
    req = PatientProfileRequest(
        age=52,
        condition="Hypertension",
        symptoms=["headache"],
        allergies=["ACE Inhibitors"],
        current_medications=[],
    )
    resp = rec_service.get_recommendations(req)

    assert resp.patient_summary["condition"] == "Hypertension"
    assert len(resp.recommended_drugs) > 0
    assert len(resp.filtered_drugs) > 0

    # Verify that ACE inhibitor formulations are filtered due to allergy
    first_filter = resp.filtered_drugs[0]
    assert first_filter.safety_status == "FILTERED_SAFETY_CONFLICT"
    assert "ALLERGY_CONFLICT" in first_filter.exact_rule_triggered
    assert first_filter.severity in ("HIGH", "CRITICAL")
    assert any("ACE Inhibitors" in f.clinical_reason for f in resp.filtered_drugs)

    # Verify that no recommended drug has ACE Inhibitor conflict
    for rec in resp.recommended_drugs:
        assert rec.safety_status in ("NO_KNOWN_CONFLICT", "WARNING")



def test_recommendation_service_with_ddi_warning(rec_service):
    """
    Test that taking Potassium Chloride with an interacting medication triggers interaction audit.
    """
    req = PatientProfileRequest(
        age=45,
        condition="Hypertension",
        symptoms=["elevated blood pressure"],
        allergies=[],
        current_medications=["Potassium Chloride"],
    )
    resp = rec_service.get_recommendations(req)

    assert len(resp.recommended_drugs) > 0 or len(resp.filtered_drugs) > 0


def test_api_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "connected" in data["database"]
    assert data["models_loaded"] is True


def test_api_conditions(client):
    response = client.get("/api/v1/conditions")
    assert response.status_code == 200
    data = response.json()
    assert data["total_conditions"] > 800
    assert len(data["conditions"]) > 0
    assert "condition_id" in data["conditions"][0]


def test_api_allergies(client):
    response = client.get("/api/v1/allergies")
    assert response.status_code == 200
    data = response.json()
    assert len(data["allergen_classes"]) > 0
    assert "ACE Inhibitors" in data["allergen_classes"]
    assert "Penicillins" in data["allergen_classes"]


def test_api_drugs_list_and_detail(client):
    # List drugs
    list_resp = client.get("/api/v1/drugs?limit=5")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total_drugs"] > 3000
    assert len(list_data["drugs"]) == 5

    first_drug_id = list_data["drugs"][0]["drug_id"]

    # Detail query
    detail_resp = client.get(f"/api/v1/drugs/{first_drug_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["drug_id"] == first_drug_id
    assert "indicated_conditions" in detail_data
    assert "allergy_classes" in detail_data
    assert "contraindications" in detail_data


def test_api_sentiment_analyze(client):
    payload = {"text": "Excellent drug, worked immediately to relieve severe migraine pain with no adverse effects."}
    response = client.post("/api/v1/sentiment/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_sentiment"] == "Positive"
    assert 0.50 <= data["polarity_score"] <= 1.0
    assert len(data["top_keywords"]) > 0


def test_api_recommend_endpoint(client):
    payload = {
        "age": 40,
        "condition": "High Blood Pressure",
        "symptoms": ["headache", "dizziness"],
        "allergies": ["ACE Inhibitors"],
        "current_medications": [],
        "weights": {
            "condition_match": 0.40,
            "similarity": 0.30,
            "sentiment": 0.20,
            "rating": 0.10,
        },
    }
    response = client.post("/api/v1/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "patient_summary" in data
    assert "applied_weights" in data
    assert "recommended_drugs" in data
    assert "filtered_drugs" in data
    assert "disclaimer" in data
    assert "NO_KNOWN_CONFLICT indicates only that no matching rule was triggered" in data["disclaimer"]

    # Check ACE Inhibitor filtering
    assert len(data["filtered_drugs"]) > 0
    assert any("ACE Inhibitors" in f["clinical_reason"] for f in data["filtered_drugs"])



def test_api_model_metrics(client):
    response = client.get("/api/v1/model/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["model_evaluated"] is True
    assert data["sentiment_model"]["accuracy"] == 0.8023
    assert data["sentiment_model"]["f1_macro"] == 0.709
    assert data["sentiment_model"]["test_samples"] == 53200
