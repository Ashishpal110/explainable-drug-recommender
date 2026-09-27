# API Design Specification: Explainable Personalized Drug Recommendation System

## 1. Overview

The backend exposes a lightweight, strictly typed RESTful API built on **FastAPI** with **Pydantic v2** validation.

- **Base Route**: `/api/v1`
- **Default Format**: `application/json`
- **Mandatory Compliance**: All recommendation payloads include an explicit educational and research disclaimer.

---

## 2. API Endpoint Matrix

| Method | Endpoint | Description | Primary Module |
|---|---|---|---|
| `POST` | `/api/v1/recommend` | Main personalized recommendation and independent safety screening endpoint | Modules 1, 4, 5, 6 |
| `POST` | `/api/v1/sentiment/analyze` | Standalone NLP sentiment inference on raw review text | Module 3 |
| `GET`  | `/api/v1/conditions` | List available conditions and sample symptom suggestions | Module 1, 2 |
| `GET`  | `/api/v1/allergies` | List recognized allergen and pharmacological classes | Module 1, 5 |
| `GET`  | `/api/v1/drugs` | Search and filter cataloged medications | Module 2 |
| `GET`  | `/api/v1/drugs/{drug_id}` | Detailed drug profile, review statistics, and safety rules | Module 2, 5 |
| `GET`  | `/api/v1/model/metrics` | Model performance metrics (populated after offline model evaluation) | Module 3, 6 |
| `GET`  | `/api/v1/health` | Service and model readiness check | System |

---

## 3. Detailed Endpoint Specifications

### 1. `POST /api/v1/recommend`
Executes condition matching, candidate scoring, review sentiment aggregation, independent deterministic safety screening, and factor-level explainability decomposition.

#### Request Body Schema (`PatientProfileRequest`)
```json
{
  "age": 52,
  "condition": "Hypertension",
  "symptoms": ["headache", "fatigue"],
  "allergies": ["ACE Inhibitors"],
  "current_medications": ["Potassium Chloride"],
  "weights": {
    "condition_match": 0.40,
    "similarity": 0.30,
    "sentiment": 0.20,
    "rating": 0.10
  }
}
```

#### Response Body Schema (`RecommendationResponse`)
*(Values below are illustrative examples demonstrating schema structure)*

```json
{
  "patient_summary": {
    "age": 52,
    "condition": "Hypertension",
    "symptoms": ["headache", "fatigue"],
    "allergies": ["ACE Inhibitors"],
    "current_medications": ["Potassium Chloride"]
  },
  "applied_weights": {
    "condition_match": 0.40,
    "similarity": 0.30,
    "sentiment": 0.20,
    "rating": 0.10
  },
  "recommended_drugs": [
    {
      "drug_id": 102,
      "drug_name": "Amlodipine",
      "generic_name": "amlodipine besylate",
      "drug_class": "Calcium Channel Blocker",
      "final_score": 0.865,
      "factors": {
        "condition_match": 0.95,
        "similarity_score": 0.88,
        "sentiment_score": 0.82,
        "rating_score": 0.81
      },
      "review_summary": {
        "positive_ratio": 0.82,
        "total_reviews": 412,
        "average_rating": 8.1
      },
      "safety_status": "NO_KNOWN_CONFLICT",
      "safety_details": {
        "allergy_conflict": false,
        "ddi_warnings": [],
        "contraindications": []
      },
      "explanation": "Recommended because this medication has a strong condition match for Hypertension with positive patient-reported review sentiment. No matching conflict was found in the local safety knowledge base."
    }
  ],
  "filtered_drugs": [
    {
      "drug_id": 105,
      "drug_name": "Lisinopril",
      "raw_recommendation_score": 0.895,
      "factors": {
        "condition_match": 0.96,
        "similarity_score": 0.91,
        "sentiment_score": 0.84,
        "rating_score": 0.80
      },
      "safety_status": "FILTERED_SAFETY_CONFLICT",
      "exact_rule_triggered": "ALLERGY_CONFLICT_AND_HIGH_SEVERITY_DDI",
      "affected_items": [
        "Allergy Class: ACE Inhibitors",
        "Interacting Medication: Potassium Chloride"
      ],
      "severity": "HIGH",
      "clinical_reason": "Patient profile includes recorded allergy to ACE Inhibitors and concurrent use of Potassium Chloride, which interacts with ACE Inhibitors.",
      "explanation": "Filtered due to safety constraints: Lisinopril belongs to the ACE Inhibitor allergen class and exhibits a severe interaction rule with Potassium Chloride in the local safety database."
    }
  ],
  "disclaimer": "This is an academic research and decision-support prototype. The status NO_KNOWN_CONFLICT indicates only that no matching rule was triggered in the local database and does NOT establish clinical safety. This system does not provide medical advice or replace a qualified healthcare professional."
}
```

---

### 2. `POST /api/v1/sentiment/analyze`
Evaluates arbitrary patient review text using the trained TF-IDF + Logistic Regression model.

#### Request Body (`SentimentAnalysisRequest`)
```json
{
  "text": "Effective medication for symptom control with minimal reported side effects."
}
```

#### Response Body (`SentimentAnalysisResponse`)
*(Illustrative schema example)*
```json
{
  "predicted_sentiment": "Positive",
  "polarity_score": 0.875,
  "confidence": 0.912,
  "top_keywords": ["effective", "symptom control", "minimal side effects"]
}
```

---

### 3. `GET /api/v1/conditions`
Returns indexed medical conditions dynamically queried from the SQLite store.

#### Response Body Schema
*(Illustrative schema example)*
```json
{
  "total_conditions": 0,
  "conditions": [
    {
      "condition_id": 1,
      "name": "Hypertension",
      "category": "Cardiovascular",
      "drug_count": 0
    }
  ]
}
```

---

### 4. `GET /api/v1/allergies`
Returns recognized allergen and pharmacological classes supported by the safety crosswalk.

#### Response Body Schema
*(Illustrative schema example)*
```json
{
  "allergen_classes": [
    "ACE Inhibitors",
    "Beta Blockers",
    "Macrolides",
    "NSAIDs",
    "Opioids",
    "Penicillins",
    "Statins",
    "Sulfa drugs"
  ]
}
```

---

### 5. `GET /api/v1/drugs`
Paginated search and listing of cataloged medications dynamically queried from SQLite.

#### Query Parameters:
- `condition` (Optional, string)
- `search` (Optional, string)
- `limit` (Optional, integer, default 50)
- `offset` (Optional, integer, default 0)

#### Response Body Schema
```json
{
  "total_drugs": 0,
  "limit": 50,
  "offset": 0,
  "drugs": [
    {
      "drug_id": 1,
      "name": "Amlodipine",
      "generic_name": "amlodipine besylate",
      "drug_class": "Calcium Channel Blocker",
      "avg_rating": 0.0,
      "total_reviews": 0,
      "positive_sentiment_ratio": 0.0
    }
  ]
}
```

---

### 6. `GET /api/v1/drugs/{drug_id}`
Returns detailed profile, review statistics, indicated conditions, and seeded safety rules for a specific drug.

#### Response Body Schema
```json
{
  "drug_id": 102,
  "name": "Amlodipine",
  "generic_name": "amlodipine besylate",
  "drug_class": "Calcium Channel Blocker",
  "description": "Dihydropyridine calcium channel blocker used in the management of hypertension.",
  "avg_rating": 0.0,
  "total_reviews": 0,
  "positive_sentiment_ratio": 0.0,
  "indicated_conditions": [],
  "allergy_classes": [],
  "contraindications": [],
  "interaction_count": 0
}
```

---

### 7. `GET /api/v1/model/metrics`
Returns evaluation metrics for the NLP sentiment model and recommendation engine. 

> [!NOTE]
> Values are populated dynamically after model training and evaluation on the test dataset. Metric fields are `null` if the model has not yet undergone offline evaluation.

#### Response Body Schema
```json
{
  "model_evaluated": false,
  "sentiment_model": {
    "model_name": "TF-IDF + Logistic Regression",
    "supervision_method": "Rating-derived proxy labels (Pos >= 7, Neu 5-6, Neg <= 4)",
    "accuracy": null,
    "precision_macro": null,
    "recall_macro": null,
    "f1_macro": null,
    "classes": ["Negative", "Neutral", "Positive"],
    "evaluation_dataset_split": "Drugs.com Holdout Test Split (drugsComTest_raw.tsv)"
  },
  "recommendation_engine": {
    "algorithm": "Content-Based Cosine Similarity + Review Sentiment Weighting",
    "feature_representation": "TF-IDF Vector Space (Condition, Profile, Review Aspects)"
  }
}
```

---

### 8. `GET /api/v1/health`
System status, database connectivity, and model artifact readiness probe.

#### Response Body Schema
```json
{
  "status": "healthy",
  "database": "connected",
  "models_loaded": false,
  "version": "1.0.0"
}
```

---

## 4. Error Handling & HTTP Status Codes

- `200 OK`: Request succeeded.
- `400 Bad Request`: Invalid patient parameters (e.g., negative age, missing required condition).
- `404 Not Found`: Requested drug or condition ID not found in database.
- `422 Unprocessable Entity`: Schema validation failure in request body.
- `500 Internal Server Error`: Internal processing error.

All error payloads adhere to standard JSON:
```json
{
  "detail": "Description of the validation or operational error",
  "error_code": "INVALID_PROFILE_DATA"
}
```
