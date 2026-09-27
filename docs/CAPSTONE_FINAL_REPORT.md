# Explainable Personalized Drug Recommendation and Safety Screening System Using Machine Learning
**B.Tech Final-Year Capstone Project Report**

---

## Abstract

Machine learning in clinical decision support often suffers from the "black-box" dilemma, where statistical recommendations fail to guarantee adherence to clinical safety constraints such as drug allergies, severe drug-drug interactions (DDIs), and patient contraindications. 

This project presents an **Explainable Personalized Drug Recommendation and Safety Screening System**, featuring a decoupled two-tier architecture that synthesizes data-driven recommendation scoring with deterministic, rule-based clinical safety verification. 

The recommendation pipeline evaluates patient conditions, reported symptoms, historical satisfaction ratings, and model-inferred patient review sentiment using a Term Frequency-Inverse Document Frequency (TF-IDF) representation coupled with a class-balanced Logistic Regression model trained on 159,498 patient reviews and evaluated on 53,200 holdout reviews from the Drugs.com corpus. The NLP sentiment model achieves an empirical accuracy of **80.23%**, a macro F1-score of **0.7090**, and a weighted F1-score of **0.8182** under rating-derived proxy supervision.

Crucially, safety evaluation is decoupled from statistical scoring: candidates are independently audited by a deterministic safety engine backed by a relational SQLite knowledge base containing verified allergy crosswalks, canonical drug interaction pairs ($A < B$), and contraindications sourced from FDA SPL and DailyMed labels. High-severity conflicts strictly divert candidates to a filtered conflict view with exact rule provenance, preventing dangerous overrides by statistical recommendation scores. The system is served via an asynchronous FastAPI backend and an interactive React/Vite dashboard, providing human-interpretable factor decompositions and clear clinical decision-support justifications.

---

## 1. Introduction

### 1.1 Background & Motivation
Adverse Drug Events (ADEs) represent a leading cause of preventable morbidity and healthcare expenditure globally. While artificial intelligence and natural language processing hold immense promise for mining real-world patient feedback and tailoring therapy to clinical indications, standard recommendation systems (e.g., collaborative filtering or pure content-based vector embeddings) optimize exclusively for user preference or semantic similarity.

In pharmacotherapy, prioritizing a drug solely because past patients reported high satisfaction is clinically perilous if the patient has a severe hypersensitivity to that drug class or takes a concurrent medication with life-threatening interaction potential (e.g., co-prescribing an ACE inhibitor with potassium supplements).

### 1.2 Problem Statement
Existing biomedical recommendation systems exhibit three primary shortcomings:
1. **Lack of Safety Constraint Guarantees**: Soft mathematical penalties for contraindications in loss functions can still permit unsafe drugs to rank highly if their positive review signals are strong.
2. **Opacity and Black-Box Inferences**: Deep neural embeddings often fail to explain *why* a particular medication is suggested or *why* another was omitted.
3. **Misalignment of User Experience and Clinical Efficacy**: User reviews reflect patient-reported satisfaction and tolerability, which must be clearly differentiated from formal clinical trial efficacy.

### 1.3 Contributions of this Work
- **Decoupled Architecture**: Separation of statistical recommendation scoring from deterministic safety verification.
- **Traceable Safety Knowledge Base**: Implementation of canonical, verifiable safety rules derived from official FDA labeling.
- **Explainable Factor Decomposition**: Linear transparency breaking down scores into Indication Match, Symptom Similarity, Review Sentiment, and Rating Score.
- **Academic Decision-Support Prototype**: Complete full-stack implementation with FastAPI, scikit-learn, SQLite, and React.

---

## 2. Literature & Technological Background

### 2.1 Content-Based Filtering in Healthcare
Content-based recommendation systems map user queries and item characteristics into a shared vector space, typically using cosine similarity over TF-IDF features or dense neural embeddings (e.g., BioBERT). While neural language models capture rich semantic contexts, linear TF-IDF combined with regularized linear classifiers provides deterministic feature attributions, rapid inference latency ($<50\text{ms}$), and full interpretability.

### 2.2 Review Sentiment Analysis as Proxy Supervision
Clinical datasets rarely possess explicit binary satisfaction labels. In biomedical informatics, numerical patient ratings ($1\text{--}10$) serve as a standardized proxy ground truth to supervise NLP classifiers. Training classifiers on review text allows the system to evaluate nuanced patient feedback and infer sentiment polarity on unrated text queries.

### 2.3 Rule-Based Clinical Decision Support Systems (CDSS)
Deterministic expert systems remain the gold standard in clinical pharmacology for checking drug-drug interactions and allergies because medical rules require zero tolerance for stochastic hallucination or probabilistic error.

---

## 3. Methodology & System Architecture

```
                                  [ Patient Profile Request ]
                               (Age, Condition, Symptoms, Allergies, Meds)
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      ▼                                             ▼
        [ Tier 1: Recommendation Pipeline ]           [ Tier 2: Deterministic Safety Layer ]
        - SQLite Indication Mapping Candidate Query  - Allergy Crosswalk Matching (Allergen Class)
        - TF-IDF Cosine Symptom Similarity (Sim)     - Unordered DDI Pair Audit (drug_a_id < drug_b_id)
        - Model-Inferred Review Sentiment (S_sent)   - Age & Condition Contraindication Logic
        - Normalized Historical Rating (R_rating)                   │
                      │                                             │
                      ▼                                             ▼
        [ Raw Recommendation Score (0.0 - 1.0) ]       [ Safety Audit Result (Independent) ]
                      │                                             │
                      └──────────────────────┬──────────────────────┘
                                             │
                                             ▼
                      [ Safety-Aware Ranking & Explainability Engine ]
                                             │
                        ┌────────────────────┴────────────────────┐
                        ▼                                         ▼
         Safety Status == NO_KNOWN_CONFLICT / WARNING       Safety Status == FILTERED_SAFETY_CONFLICT
                        │                                         │
                        ▼                                         ▼
           [ Recommended Medications ]                   [ Filtered Unsafe Candidates ]
         - Final Score & Rank                          - Raw Suppressed Score
         - 4-Factor Breakdown                          - Violated Rule & Affected Items
         - Review Satisfaction Metrics                 - Severity & Clinical Reason
         - Natural Language Explanation                - Contraindication Justification
```

### 3.1 Recommendation Scoring Function
For a candidate drug $d$ under condition $c$, the raw recommendation score is defined as:

$$\text{Score}_{\text{raw}}(d, c) = w_{\text{cond}} \cdot \text{Match}_{\text{cond}}(d, c) + w_{\text{sim}} \cdot \text{Sim}_{\text{content}}(q, d) + w_{\text{sent}} \cdot \bar{S}_{\text{sentiment}}(d) + w_{\text{rat}} \cdot R_{\text{rating}}(d, c)$$

Where:
- $\text{Match}_{\text{cond}}(d, c) \in [0.80, 1.00]$ scales indication evidence by review volume.
- $\text{Sim}_{\text{content}}(q, d) \in [0.0, 1.0]$ represents the TF-IDF cosine similarity between the symptom query $q$ and indication context.
- $\bar{S}_{\text{sentiment}}(d) \in [0.0, 1.0]$ is the mean predicted probability of positive patient sentiment across all corpus reviews for drug $d$.
- $R_{\text{rating}}(d, c) = \frac{\text{Rating}}{10.0} \in [0.0, 1.0]$ is the normalized historical satisfaction rating.
- Default weights: $w_{\text{cond}} = 0.40, w_{\text{sim}} = 0.30, w_{\text{sent}} = 0.20, w_{\text{rat}} = 0.10$ ($\sum w_i = 1.0$).

### 3.2 Safety Decoupling & Status Semantics
Safety evaluation is strictly independent. A candidate drug is assigned one of three mutually exclusive safety statuses:
1. **`NO_KNOWN_CONFLICT`**: No matching rule was triggered in the local SQLite knowledge base. *(Does not establish clinical safety)*.
2. **`WARNING`**: A moderate DDI or non-fatal precaution was detected. The drug is presented with an amber alert banner and clinical monitoring notes.
3. **`FILTERED_SAFETY_CONFLICT`**: A severe allergy conflict, high-severity DDI, or absolute contraindication was triggered. The drug is excluded from recommendations and displayed in a dedicated filtered audit panel.

---

## 4. Database Design

The relational database (`data/processed/drug_system.db`) is structured into two distinct layers:

### Layer 1: Indication & Review Schema
- **`drugs`**: Primary medication catalog ($3,654$ records) containing drug names, generic names, pharmacological classes, aggregate review counts, average ratings, and positive sentiment ratios.
- **`conditions`**: Standardized indications ($836$ records) cataloged from patient records.
- **`drug_conditions`**: M:N indication mapping ($8,586$ records) linking drugs to specific medical indications with condition-specific review counts and ratings.

### Layer 2: Deterministic Safety Knowledge Base
- **`allergy_crosswalk`**: Maps drug IDs to recognized allergen classes (e.g., ACE Inhibitors, NSAIDs, Penicillins, Beta Blockers) with reaction severity and clinical citations.
- **`drug_interactions`**: Stores bidirectional interaction pairs using a canonical foreign-key constraint (`drug_a_id < drug_b_id`) with severity ratings, interaction mechanisms, and clinical actions.
- **`contraindications`**: Stores rule-based contraindications categorized by type (`AGE`, `CONDITION`, `PREGNANCY`) with relational trigger expressions (e.g., `<18`).

---

## 5. Machine Learning Evaluation & Results

### 5.1 Dataset Split & Class Distribution
The Drugs.com review corpus was partitioned into training ($75\%$, $159,498$ rows) and holdout test ($25\%$, $53,200$ rows) splits:
- **Positive ($\ge 7$)**: $35,083$ test reviews ($65.9\%$)
- **Negative ($\le 4$)**: $13,355$ test reviews ($25.1\%$)
- **Neutral ($5\text{--}6$)**: $4,762$ test reviews ($9.0\%$)

### 5.2 Model Performance Metrics
Training on $159,498$ samples with a 35,000-feature unigram/bigram TF-IDF vectorizer and class-balanced Logistic Regression required **22.19 seconds**. Holdout evaluation across all 53,200 test samples yielded:

| Evaluation Metric | Holdout Score |
| :--- | :---: |
| **Overall Accuracy** | **80.23%** (0.8023) |
| **Macro Precision** | **0.6902** |
| **Macro Recall** | **0.7601** |
| **Macro F1-Score** | **0.7090** |
| **Weighted F1-Score** | **0.8182** |

### 5.3 Per-Class Classification Report

| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Positive** | 0.9454 | 0.8237 | 0.8804 | 35,083 |
| **Negative** | 0.7646 | 0.7966 | 0.7803 | 13,355 |
| **Neutral** | 0.3606 | 0.6600 | 0.4664 | 4,762 |

### 5.4 Confusion Matrix
```
                     Predicted Negative   Predicted Neutral   Predicted Positive
Actual Negative :          10,639               1,788                 928
Actual Neutral  :             878               3,143                 741
Actual Positive :           2,398               3,786              28,899
```

---

## 6. System Verification & Quality Assurance

### 6.1 Automated Test Suites
A total of **38 automated unit and integration test cases** were executed via pytest across the following modules:
- `test_health.py`: System status and model artifact presence.
- `test_preprocessing_db.py`: Text cleaning, HTML unescaping, proxy labeling, and foreign key integrity.
- `test_safety_engine.py`: Deterministic rule matching, allergy crosswalks, DDI lookups, and contraindications.
- `test_sentiment_model.py`: Inference latency, probability boundaries, and salient keyword extraction.
- `test_recommendation_engine.py`: Multi-factor weight normalization and indication ranking.
- `test_recommendation_api.py`: FastAPI end-to-end integration and Pydantic validation.

**Result**: 38/38 tests passed ($100\%$ pass rate, execution time $5.74\text{s}$).

### 6.2 Latency & Performance Benchmarks
- Health Check (`GET /api/v1/health`): **$3.68\text{ ms}$**
- Recommendation Pipeline (`POST /api/v1/recommend`): **$233.53\text{ ms}$**
- Sentiment Inference (`POST /api/v1/sentiment/analyze`): **$46.96\text{ ms}$**
- Drug Catalog Query (`GET /api/v1/drugs?limit=50`): **$5.11\text{ ms}$**
- Condition Index Query (`GET /api/v1/conditions`): **$10.38\text{ ms}$**

---

## 7. Limitations & Ethical Considerations

1. **Non-Prescription Prototype**: The system is an educational decision-support prototype. It does not replace medical consultation.
2. **Local Safety Completeness**: `NO_KNOWN_CONFLICT` signifies only that no matching rule was found in the local SQLite knowledge base; it is not clinical proof of safety.
3. **Proxy Label Subjectivity**: Review sentiment reflects patient experience and satisfaction rather than double-blind randomized clinical trial efficacy.
4. **Demographic Variables**: Gender was excluded to prevent demographic bias in recommendation scoring.

---

## 8. Future Scope

- **Integration with Standard Ontologies**: Expanding the knowledge base with RxNorm, ATC, and SNOMED-CT identifiers.
- **Biomedical Entity Linking**: Integrating NER models (e.g., Med7) to parse unstructured clinical notes directly.
- **Multi-Modal Patient Factors**: Incorporating renal function (eGFR) and hepatic parameters into deterministic contraindication rules.

---

## 9. Conclusion

The Explainable Personalized Drug Recommendation and Safety Screening System demonstrates that statistical machine learning and deterministic clinical rule engines can be harmoniously integrated. By decoupling recommendation scoring from safety verification, the architecture ensures that patient-reported satisfaction insights enhance decision support without compromising patient safety.

---

## 10. References

1. Gräßer, F., Kallumadi, S., Malberg, H., & Zaunseder, S. (2018). Aspect-Based Sentiment Analysis of Drug Reviews Applying Cross-Domain and Cross-Data Learning. *Proceedings of the 2018 International Conference on Digital Health (DH '18)*, 121–125.
2. FDA Structured Product Labeling (SPL) Standard & DailyMed National Library of Medicine Database.
3. Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.
4. Tiangolo, S. (2018). FastAPI: Modern, fast (high-performance), web framework for building APIs with Python.
