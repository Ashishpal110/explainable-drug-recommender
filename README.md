# Explainable Personalized Drug Recommendation and Safety Screening System Using Machine Learning

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18_%2B_Vite-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![SQLite](https://img.shields.io/badge/Database-SQLite_3-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org)
[![Tests](https://img.shields.io/badge/Tests-38%2F38_Passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Academic B.Tech Final-Year Capstone Project**  
> *A Clinical Decision-Support Prototype with Decoupled Deterministic Safety Auditing*  
> **Author:** [Ashish Pal](https://github.com/Ashishpal110)

---

## ⚠️ Mandatory Educational & Research Disclaimer

> [!IMPORTANT]
> **This system is an academic research and clinical decision-support prototype. It does NOT provide medical advice, diagnosis, or prescriptions.**  
> The safety status `NO_KNOWN_CONFLICT` indicates only that **no matching allergy, drug-drug interaction (DDI), or contraindication rule was found in the local database**. It does **NOT** establish or prove clinical safety. All recommendations must be reviewed by a qualified healthcare professional.

---

## 1. Project Overview

The **Explainable Personalized Drug Recommendation and Safety Screening System** addresses a critical limitation in healthcare AI: the black-box nature of statistical recommendation systems.

In real-world pharmacotherapy, suggesting medications solely based on review satisfaction ratings or keyword similarity is hazardous if patient-specific safety constraints (such as severe drug allergies, drug-drug interactions, or pediatric contraindications) are ignored.

This system implements a **two-tier decoupled architecture**:
1. **Multi-Factor Content-Based Recommendation Pipeline**: Discovers candidates based on indication match, TF-IDF profile similarity, model-inferred patient review satisfaction, and historical patient ratings.
2. **Deterministic Safety Screening Engine**: An independent, deterministic rule-based safety layer that audits every candidate against structured SQLite knowledge base tables (allergy crosswalk, DDI rules, and contraindications) with verifiable clinical sources (FDA SPL / DailyMed).

---

## 2. Key Architectural Principles

- **Strict Decoupling**: Recommendation factor scoring ($Match_{cond}$, $Sim_{content}$, $\bar{S}_{sentiment}$, $R_{rating}$) operates independently from safety evaluation. Safety compatibility is **NOT** a recommendation scoring factor.
- **Safety Overrides Score**: If a candidate triggers a high/critical safety conflict (e.g., severe allergy or severe DDI), it is strictly diverted to `filtered_drugs` regardless of how high its recommendation score might be.
- **Explainability by Design**: Every recommendation and every filtered exclusion includes transparent mathematical factor contributions and natural language justifications.
- **Proxy Supervision**: NLP sentiment classification utilizes rating-derived proxy labels ($\ge 7$ Positive, $5\text{--}6$ Neutral, $\le 4$ Negative) and reflects patient-reported satisfaction rather than clinical trial efficacy.
- **No Gender Dependence**: Patient profiles strictly contain age, condition, optional symptoms, allergies, and active medications.

---

## 3. Technology Stack

### Backend
- **Framework**: FastAPI (Asynchronous REST API)
- **Language**: Python 3.10+ (Tested on Python 3.14.6)
- **Data Validation**: Pydantic v2
- **Database**: SQLite 3 (with enforced `PRAGMA foreign_keys = ON;`)
- **Data Science & ML**: pandas, NumPy, scikit-learn, joblib
- **Testing**: pytest, httpx

### Frontend
- **Framework**: React 18 + Vite
- **Routing**: React Router DOM
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Visuals**: Recharts

---

## 4. System Architecture

```text
                                  [ Patient Profile Request ]
                           (Age, Condition, Symptoms, Allergies, Meds)
                                               │
                        ┌──────────────────────┴──────────────────────┐
                        ▼                                             ▼
          [ Tier 1: Recommendation Pipeline ]           [ Tier 2: Deterministic Safety Layer ]
          • Medical Indication Match (0.40)             • Allergy Crosswalk (30 rules)
          • TF-IDF Profile Similarity (0.30)            • Drug-Drug Interactions (18 pairs)
          • NLP Review Sentiment (0.20)                 • Age/Condition Contraindications
          • Historical Patient Rating (0.10)            • Sourced from FDA SPL / DailyMed
                        │                                             │
                        └──────────────────────┬──────────────────────┘
                                               ▼
                                 [ Recommendation Service ]
                           • Evaluates candidate safety status
                           • NO_KNOWN_CONFLICT / WARNING       → recommended_drugs
                           • FILTERED_SAFETY_CONFLICT          → filtered_drugs
                                               │
                                               ▼
                                    [ Structured JSON API ]
                                  + Factor Breakdowns & Disclaimer
                                               │
                                               ▼
                                    [ React 18 Dashboard ]
```

---

## 5. Repository Structure

```text
explainable-drug-recommender/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── drugs.py           # Catalog routes (drugs, conditions, allergies)
│   │   │   │   ├── health.py          # System status and readiness probe
│   │   │   │   ├── metrics.py         # Empirical model evaluation metrics
│   │   │   │   ├── recommend.py       # Recommendation and safety screening endpoint
│   │   │   │   └── sentiment.py       # NLP review sentiment analysis endpoint
│   │   │   └── __init__.py            # API router aggregator
│   │   ├── core/
│   │   │   └── config.py              # Application settings and directory paths
│   │   ├── db/
│   │   │   ├── database.py            # SQLite schema initialization and connection helpers
│   │   │   └── models.py              # SQL schema definitions
│   │   ├── ml/
│   │   │   ├── preprocessing.py       # HTML entity decoding and text normalization
│   │   │   ├── recommendation.py      # ContentRecommender scoring pipeline
│   │   │   └── sentiment.py           # SentimentModel inference wrapper
│   │   ├── safety/
│   │   │   └── screening.py           # Deterministic SafetyScreeningEngine
│   │   ├── schemas/
│   │   │   ├── recommendation.py      # Pydantic request/response schemas
│   │   │   └── sentiment.py           # Sentiment request/response schemas
│   │   ├── services/
│   │   │   ├── explanation_service.py # Natural language justification generator
│   │   │   └── recommendation_service.py # Orchestrator combining recommendation & safety
│   │   └── main.py                    # FastAPI application entrypoint
│   ├── tests/                         # Pytest test suite (38 passing tests)
│   ├── pytest.ini                     # Warning filter configurations
│   ├── requirements.txt               # Backend Python dependencies
│   └── .env.example                   # Backend environment template
│
├── frontend/
│   ├── src/
│   │   ├── components/                # Modular UI components
│   │   │   ├── DisclaimerBanner.jsx   # Persistent decision support disclaimer
│   │   │   ├── ErrorState.jsx         # Error handling with retry
│   │   │   ├── ExplanationPanel.jsx   # Natural language explanation panel
│   │   │   ├── FactorBreakdown.jsx    # 4-factor recommendation breakdown
│   │   │   ├── FilteredDrugCard.jsx   # Excluded unsafe candidate card
│   │   │   ├── LoadingState.jsx       # Animated clinical loading spinner
│   │   │   ├── PatientProfileForm.jsx # Profile intake (age, condition, allergies, meds)
│   │   │   ├── RecommendationCard.jsx # Approved candidate recommendation card
│   │   │   ├── ReviewSummary.jsx      # Historical patient satisfaction summary
│   │   │   └── SafetyBadge.jsx        # Strict safety status badge
│   │   ├── pages/                     # Application views
│   │   │   ├── Conditions.jsx         # Indexed medical conditions directory
│   │   │   ├── Dashboard.jsx          # Main recommendation and safety dashboard
│   │   │   ├── DrugDetails.jsx        # Drug profile and safety rule inspection
│   │   │   ├── DrugExplorer.jsx       # Searchable, paginated medication catalog
│   │   │   ├── ModelMetrics.jsx       # Holdout evaluation metrics and confusion matrix
│   │   │   └── SentimentAnalyzer.jsx  # Interactive review text sentiment analyzer
│   │   ├── services/
│   │   │   └── api.js                 # Unified frontend API client
│   │   ├── App.jsx                    # Application layout and React Router
│   │   ├── index.css                  # Tailwind styles
│   │   └── main.jsx                   # React entrypoint
│   ├── package.json                   # Frontend npm configuration
│   ├── tailwind.config.js             # Tailwind CSS configuration
│   ├── vite.config.js                 # Vite build configuration
│   └── .env.example                   # Frontend environment template
│
├── data/
│   ├── processed/
│   │   ├── drug_system.db             # Relational SQLite database (Layer 1 + Layer 2)
│   │   ├── drugs_cleaned_train.csv    # Cleaned training corpus (159,498 rows)
│   │   └── drugs_cleaned_test.csv     # Cleaned holdout test corpus (53,200 rows)
│   └── safety/
│       └── verified_safety_rules.json # Traceable safety rules with clinical source citations
│
├── models/
│   ├── sentiment_vectorizer.joblib    # Serialized TF-IDF feature extractor (10,000 features)
│   ├── sentiment_model.joblib         # Serialized Logistic Regression classifier
│   ├── sentiment_metrics.json         # Empirical holdout test set evaluation results
│   └── drug_sentiment_scores.joblib   # Aggregated S_sentiment for 3,654 medications
│
├── scripts/
│   ├── e2e_http_integration_test.py   # E2E socket HTTP test suite
│   └── phase9_comprehensive_evaluation.py # Comprehensive evaluation runner
│
├── docs/                              # Finalized architecture and project documentation
│   ├── API_DESIGN.md
│   ├── CAPSTONE_FINAL_REPORT.md       # Comprehensive academic final report
│   ├── DATABASE_DESIGN.md
│   ├── DATASET_PLAN.md
│   ├── DEMO_GUIDE.md                  # Demonstration script and scenario walkthrough
│   ├── FINAL_SUBMISSION_CHECKLIST.md  # Official submission verification checklist
│   ├── PHASE_9_TESTING_EVALUATION_REPORT.md # Empirical evaluation report
│   ├── PHASE_10_FINAL_RELEASE_REPORT.md    # Final release report
│   ├── SYSTEM_ARCHITECTURE.md
│   └── VIVA_PRESENTATION_GUIDE.md     # Presentation deck & viva defense Q&A
│
├── requirements.txt                   # Root Python dependencies
├── .gitignore                         # Standard clean gitignore
├── .env.example                       # Root environment template
├── LICENSE                            # MIT License
└── README.md
```

---

## 6. Dataset & Preprocessing

The primary dataset is derived from the **UCI / Drugs.com Drug Review Corpus** (215,063 raw records):
- **Train Split (`drugs_cleaned_train.csv`)**: 159,498 rows
- **Test Split (`drugs_cleaned_test.csv`)**: 53,200 rows

### Preprocessing Pipeline:
1. **HTML Entity Decoding**: Unescapes doubly-encoded entities (e.g., `&#039;` $\rightarrow$ `'`, `&amp;` $\rightarrow$ `&`).
2. **Noise & Web Artifact Removal**: Strips residual HTML tags (`<br>`, `<span>`) and invalid community count artifacts.
3. **Rating-Derived Proxy Labeling**:
   - `Positive`: Rating $\ge 7/10$
   - `Neutral`: Rating $5\text{--}6/10$
   - `Negative`: Rating $\le 4/10$
4. **Relational Database Population**: Creates 3,654 unique cataloged drugs, 836 valid conditions, and 8,586 drug-condition indication mappings in SQLite.

---

## 7. Machine Learning Methodology & Empirical Results

### Pipeline Configuration
- **Text Vectorizer**: `TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True, stop_words="english")`
- **Classification Model**: `LogisticRegression(C=1.0, solver="lbfgs", class_weight="balanced", max_iter=1000, random_state=42)`
- **Training Samples**: 159,498 patient reviews
- **Holdout Test Samples**: 53,200 patient reviews

### Empirical Holdout Evaluation (`models/sentiment_metrics.json`)

| Metric | Score | Description |
| :--- | :---: | :--- |
| **Accuracy** | **80.23%** (0.8023) | Overall classification accuracy on 53,200 holdout test reviews |
| **Macro Precision** | **0.7601** | Unweighted average precision across Positive, Neutral, Negative |
| **Macro Recall** | **0.6902** | Unweighted average recall across all 3 classes |
| **Macro F1-Score** | **0.7090** | Unweighted harmonic mean of precision and recall |
| **Weighted F1-Score** | **0.8182** | Support-weighted F1-Score reflecting class distribution |

### Confusion Matrix (Test Split)
```text
                     Predicted Negative   Predicted Neutral   Predicted Positive
Actual Negative :          10,639               1,788                 928
Actual Neutral  :             878               3,143                 741
Actual Positive :           2,398               3,786              28,899
```

---

## 8. Recommendation & Safety Architecture

### Recommendation Scoring Formula
$$\text{Score}_{\text{raw}} = w_{\text{cond}} \cdot \text{Match}_{\text{cond}} + w_{\text{sim}} \cdot \text{Sim}_{\text{content}} + w_{\text{sent}} \cdot \bar{S}_{\text{sentiment}} + w_{\text{rat}} \cdot R_{\text{rating}}$$

- **Configurable Default Weights**: $w_{\text{cond}} = 0.40, w_{\text{sim}} = 0.30, w_{\text{sent}} = 0.20, w_{\text{rat}} = 0.10$.
- **Decoupled Safety Principle**: The recommendation pipeline evaluates indication match and user experience satisfaction. The independent safety layer audits candidate drugs against SQLite safety tables.

### Safety Statuses Supported
1. **`NO_KNOWN_CONFLICT`**: No matching rule was triggered in the local SQLite knowledge base.
2. **`WARNING`**: Moderate interaction or precaution detected (candidate remains in recommendations with explicit warning banner).
3. **`FILTERED_SAFETY_CONFLICT`**: Severe allergy, high-severity DDI, or absolute contraindication detected (candidate is strictly moved to `filtered_drugs`).

---

## 9. API Specification

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | System health, database connection, and model loading status |
| `POST` | `/api/v1/recommend` | Patient profile intake, recommendation scoring, and safety screening |
| `POST` | `/api/v1/sentiment/analyze` | On-demand NLP review sentiment inference and salient keyword extraction |
| `GET` | `/api/v1/conditions` | List of indexed medical conditions with mapped drug counts |
| `GET` | `/api/v1/allergies` | Supported allergen and pharmacological classes in safety crosswalk |
| `GET` | `/api/v1/drugs` | Paginated search of cataloged medications |
| `GET` | `/api/v1/drugs/{drug_id}` | Detailed drug profile, indication list, and seeded safety rules |
| `GET` | `/api/v1/model/metrics` | Live holdout test set evaluation metrics and pipeline specifications |

---

## 10. Installation & Running Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/Ashishpal110/explainable-drug-recommender.git
cd explainable-drug-recommender
```

### 2. Backend Setup
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* **API Swagger Docs:** `http://127.0.0.1:8000/docs`
* **Health Check:** `http://127.0.0.1:8000/api/v1/health`

### 3. Frontend Setup (In a New Terminal)
```bash
cd frontend
npm install
npm run dev
```
* **Interactive UI Dashboard:** `http://localhost:5173`

### 4. Running Verification Tests
```bash
python -m pytest backend/tests/ -v
```

---

## 11. Academic Capstone Documentation

- 📖 [Capstone Final Academic Report](docs/CAPSTONE_FINAL_REPORT.md)
- 🎯 [Interactive Demonstration Script](docs/DEMO_GUIDE.md)
- 🎓 [Viva Presentation & Slide Deck Guide](docs/VIVA_PRESENTATION_GUIDE.md)
- 📊 [Phase 9 Testing & Empirical Evaluation Report](docs/PHASE_9_TESTING_EVALUATION_REPORT.md)
- 📦 [Phase 10 Final Release Report](docs/PHASE_10_FINAL_RELEASE_REPORT.md)
- ✅ [Final Submission Checklist](docs/FINAL_SUBMISSION_CHECKLIST.md)
- 📐 [System Architecture Document](docs/SYSTEM_ARCHITECTURE.md)
- 🗄️ [Database Schema Design](docs/DATABASE_DESIGN.md)
- 🔌 [API Specification](docs/API_DESIGN.md)

---

## 12. License & Academic Credits

- **Author:** [Ashish Pal](https://github.com/Ashishpal110)
- **Degree:** Bachelor of Technology (B.Tech) in Artificial Intelligence and Machine Leaning. 
- **License:** [MIT License](LICENSE)
