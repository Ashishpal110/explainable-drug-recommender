# Academic Demonstration & Viva Walkthrough Guide

> **Project**: Explainable Personalized Drug Recommendation and Safety Screening System  
> **Target Audience**: Evaluators, Examination Panelists, and Viva Examiners

---

## 1. Quick-Start Demonstration Environment

### Step 1: Launch Backend Server
Open a terminal in the project directory:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
- **Live Swagger API Documentation**: Open [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Probe**: Open [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### Step 2: Launch Frontend Client
Open a second terminal in the project directory:
```bash
cd frontend
npm run dev
```
- **Interactive UI Dashboard**: Open [http://localhost:5173](http://localhost:5173)

---

## 2. Structured Demonstration Scenarios

### DEMO 1: Baseline Indication Recommendation (No Known Conflicts)
- **Goal**: Demonstrate multi-factor recommendation scoring, symptom cosine similarity, review sentiment, and explainable factor breakdown.
- **Inputs**:
  - **Age**: `45`
  - **Condition**: `High Blood Pressure`
  - **Symptoms**: `headache, fatigue`
  - **Allergies**: *(Leave empty)*
  - **Current Medications**: *(Leave empty)*
- **Expected Outcome**:
  - Top candidate medications (e.g., `Azor`, `Amlodipine`, `Benicar`) displayed with green `No Known Conflict` badges.
  - Transparent 4-factor breakdown showing percentages for:
    1. Condition Match
    2. Profile Similarity
    3. Patient Sentiment
    4. Review Rating
  - Explainability narrative detailing positive patient satisfaction and absence of local safety rules.

---

### DEMO 2: High-Severity Allergy Conflict (`FILTERED_SAFETY_CONFLICT`)
- **Goal**: Prove that safety constraints override high recommendation scores and exclude unsafe candidates.
- **Inputs**:
  - **Age**: `52`
  - **Condition**: `High Blood Pressure`
  - **Symptoms**: `dizziness`
  - **Allergies**: `ACE Inhibitors`
  - **Current Medications**: *(Leave empty)*
- **Expected Outcome**:
  - High-scoring ACE Inhibitor medications (`Lisinopril`, `Enalapril`, `Ramipril`) are **excluded from the recommendation list**.
  - Excluded candidates appear in the **Filtered Unsafe Candidates** section with a red `Filtered Safety Conflict` badge and `HIGH / CRITICAL` severity label.
  - Justification card displays exact rule violated: `ALLERGY CONFLICT` (Source: FDA DailyMed Label).

---

### DEMO 3: Moderate Drug-Drug Interaction (`WARNING`)
- **Goal**: Demonstrate how moderate interactions remain in recommendations but provide explicit precaution warnings.
- **Inputs**:
  - **Age**: `60`
  - **Condition**: `High Blood Pressure`
  - **Symptoms**: *(Leave empty)*
  - **Allergies**: *(Leave empty)*
  - **Current Medications**: `Simvastatin`
- **Expected Outcome**:
  - `Amlodipine` is recommended with an amber `Warning / Precaution` badge.
  - An amber alert box details the interaction mechanism: *"Amlodipine inhibits CYP3A4-mediated clearance of Simvastatin, increasing systemic statin exposure and myopathy risk. Limit Simvastatin dosage to 20mg daily."*

---

### DEMO 4: Age-Based Contraindication Filtering
- **Goal**: Demonstrate rule-based contraindication evaluation.
- **Inputs**:
  - **Age**: `10` (Pediatric)
  - **Condition**: `Pain`
  - **Symptoms**: `muscle ache`
  - **Allergies**: *(Leave empty)*
  - **Current Medications**: *(Leave empty)*
- **Expected Outcome**:
  - `Tramadol` is filtered out with `FILTERED_SAFETY_CONFLICT` due to the contraindication trigger `<18` (contraindicated in pediatric patients due to respiratory depression risk).

---

### DEMO 5: Interactive NLP Review Sentiment Analysis
- **Goal**: Test raw, unstructured patient feedback against the offline-trained TF-IDF + Logistic Regression model.
- **Action**: Navigate to `/sentiment` in the navigation header.
- **Test Sample 1 (Positive)**:
  > *"This medication worked wonders for my chronic migraine! Within 30 minutes all pain stopped and I had zero adverse effects."*
  - **Result**: `Positive Sentiment` (Polarity: $>90\%$, Confidence: $>90\%$). Salient keywords: `worked wonders`, `pain stopped`.
- **Test Sample 2 (Negative)**:
  > *"Terrible experience. Caused severe nausea, extreme vomiting, racing heartbeat, and made symptoms worse."*
  - **Result**: `Negative Sentiment` (Polarity: $<5\%$). Salient keywords: `nausea`, `vomiting`, `severe`.

---

### DEMO 6: Model Evaluation Metrics Dashboard
- **Goal**: Showcase empirical evaluation results on the holdout test set (53,200 reviews).
- **Action**: Navigate to `/metrics` in the navigation header.
- **Metrics Displayed**:
  - Overall Holdout Accuracy: **`80.23%`**
  - Macro F1-Score: **`0.7090`**
  - Weighted F1-Score: **`0.8182`**
  - 3x3 Empirical Confusion Matrix (Negative, Neutral, Positive)
  - Per-class precision, recall, and F1-score breakdown.

---

## 3. Evaluator Q&A Key Points

- **Q: Does NO_KNOWN_CONFLICT mean the drug is safe?**  
  *A: No. It indicates strictly that no matching allergy, DDI, or contraindication rule was found in the local SQLite knowledge base. Clinical safety requires physician assessment.*
- **Q: Why is safety not included as a recommendation scoring factor?**  
  *A: If safety were a weighted factor, a drug with an extremely high sentiment and rating score could mathematically overcome a safety penalty. Decoupling safety ensures safety rules act as non-negotiable hard constraints.*
- **Q: How was the sentiment model supervised?**  
  *A: It uses rating-derived proxy supervision ($\ge 7$ Positive, $5\text{--}6$ Neutral, $\le 4$ Negative) from the Drugs.com corpus.*
