# Capstone Viva Examination & Presentation Guide

> **Project Title**: Explainable Personalized Drug Recommendation and Safety Screening System Using Machine Learning  
> **Degree**: Bachelor of Technology (B.Tech) in Computer Science & Engineering (AI & ML)

---

## 1. 2-to-3 Minute Project Pitch (Elevator Speech)

> *"Good morning, respected examiners.  
> Our capstone project addresses a critical vulnerability in modern healthcare AI: **the black-box nature of statistical recommendation engines and their failure to guarantee patient safety.**
> 
> In pharmacotherapy, prioritizing a medication merely because past patients reported high satisfaction can be catastrophic if the patient has a severe drug allergy or is taking an interacting medication.
> 
> To solve this, we designed and implemented a **decoupled, two-tier clinical decision-support prototype**:
> 1. **Tier 1 — Content-Based Recommendation Pipeline**: Scored through condition indication mapping, TF-IDF symptom cosine similarity, model-inferred patient review sentiment, and historical satisfaction ratings.
> 2. **Tier 2 — Deterministic Safety Screening Engine**: An independent rule-based layer that audits candidates against verifiable allergy crosswalks, drug-drug interactions, and contraindications sourced from FDA labeling.
> 
> Crucially, safety is **not** a weighted recommendation score factor. Severe safety conflicts strictly divert candidates to a filtered exclusion list, ensuring no mathematical score can ever override a clinical contraindication.
> 
> We trained our NLP sentiment classifier on 159,498 patient reviews and achieved **80.23% accuracy** and a **0.7090 macro F1-score** across 53,200 holdout test reviews. The entire system is implemented using FastAPI, scikit-learn, SQLite, and React, providing transparent factor decompositions and natural language explanations for every clinical decision."*

---

## 2. 12-Slide Presentation Structure & Speaker Notes

### Slide 1: Title & Overview
- **Title**: Explainable Personalized Drug Recommendation and Safety Screening System
- **Subtitle**: A Decoupled Decision-Support Architecture with Deterministic Safety Auditing
- **Speaker Notes**: Introduce team members, supervisor, and the central objective: bringing safety-guaranteed explainability to medical recommendations.

### Slide 2: Problem Statement & Clinical Motivation
- **Key Points**:
  - ADEs cause hundreds of thousands of preventable hospitalizations annually.
  - Standard recommender systems optimize for rating/similarity, not clinical safety.
  - Black-box deep learning models fail to provide auditable justifications.
- **Speaker Notes**: Highlight why soft penalties in loss functions are dangerous in clinical pharmacology.

### Slide 3: Decoupled Architectural Design
- **Key Points**:
  - Independent statistical recommendation scoring vs deterministic safety rules.
  - Safety statuses: `NO_KNOWN_CONFLICT`, `WARNING`, `FILTERED_SAFETY_CONFLICT`.
  - Gender removed to avoid demographic bias.
- **Speaker Notes**: Explain that `NO_KNOWN_CONFLICT` indicates only the absence of a local rule, not proof of clinical safety.

### Slide 4: Multi-Factor Recommendation Mathematical Formulation
- **Key Points**:
  - Formula: $\text{Score} = w_{\text{cond}} \text{Match}_{\text{cond}} + w_{\text{sim}} \text{Sim}_{\text{content}} + w_{\text{sent}} \bar{S}_{\text{sentiment}} + w_{\text{rat}} R_{\text{rating}}$
  - Normalized weights summing to $1.0$.
  - TF-IDF symptom cosine similarity.
- **Speaker Notes**: Emphasize that safety is decoupled and NOT in this formula.

### Slide 5: Deterministic Safety Knowledge Base & Screening Logic
- **Key Points**:
  - Layer 2 Relational Tables in SQLite: `allergy_crosswalk`, `drug_interactions`, `contraindications`.
  - Canonical ordering constraint: `drug_a_id < drug_b_id` for bidirectional DDI deduplication.
  - FDA SPL and DailyMed source citations for every rule.
- **Speaker Notes**: Explain how exact rule matching operates in $<5\text{ms}$.

### Slide 6: Dataset & NLP Preprocessing Pipeline
- **Key Points**:
  - Drugs.com Corpus (215,063 raw records $\rightarrow$ 212,698 cleaned records).
  - HTML entity decoding, noise artifact stripping.
  - Rating-derived proxy supervision ($\ge 7$ Pos, $5\text{--}6$ Neu, $\le 4$ Neg).
- **Speaker Notes**: Clarify that reviews represent patient-reported experience, not clinical trial efficacy.

### Slide 7: Model Training & Hyperparameters
- **Key Points**:
  - Feature representation: Unigram + Bigram TF-IDF (35,000 max features, sublinear term frequency).
  - Model: Logistic Regression with $L_2$ regularization and class-balanced weights.
  - Fast training: $22.19\text{s}$ on 159,498 training samples.
- **Speaker Notes**: Justify choosing Logistic Regression over complex deep neural networks for inference speed, determinism, and interpretability.

### Slide 8: Empirical Holdout Evaluation Results
- **Key Points**:
  - Test set size: 53,200 holdout reviews.
  - **Accuracy**: $80.23\%$ | **Macro F1**: $0.7090$ | **Weighted F1**: $0.8182$.
  - Per-class F1: Positive ($0.8804$), Negative ($0.7803$), Neutral ($0.4664$).
- **Speaker Notes**: Present the actual 3x3 confusion matrix and explain class support distributions.

### Slide 9: System Implementation & Tech Stack
- **Key Points**:
  - Backend: Python 3.14, FastAPI, Pydantic v2, SQLite, scikit-learn.
  - Frontend: React 18, Vite, Tailwind CSS, Lucide Icons, React Router.
  - Modular API contracts: 8 endpoints.
- **Speaker Notes**: Detail how Pydantic enforces rigorous schema validation and type safety.

### Slide 10: Quality Assurance & Verification
- **Key Points**:
  - 38/38 automated pytest test cases passing.
  - 15 deterministic scenarios (Scenarios A through O) verified.
  - Database PRAGMA integrity checks ($0$ violations).
  - Average recommendation latency: $233\text{ms}$.
- **Speaker Notes**: Emphasize engineering rigor and zero synthetic/fabricated testing.

### Slide 11: System Limitations & Ethical Considerations
- **Key Points**:
  - Academic decision-support prototype only (not a prescription system).
  - Local database rule completeness vs real-world medical complexity.
  - Patient satisfaction subjectivity.
- **Speaker Notes**: Reiterate that the prototype supports clinicians rather than replacing them.

### Slide 12: Future Scope & Conclusion
- **Key Points**:
  - Integration with RxNorm, ATC, SNOMED-CT ontologies.
  - Clinical entity extraction with biomedical NER.
  - Summary: Harmonizing machine learning with deterministic medical safety.
- **Speaker Notes**: Conclude presentation and open the floor for examination questions.

---

## 3. Likely Viva Questions & Authoritative Answers

### 1. Why did you choose a Content-Based Recommender instead of Collaborative Filtering?
**Answer**: Collaborative filtering relies on user-item interaction matrices (which patient took which drug). In healthcare, patient histories are sparse, protected by strict privacy (HIPAA/GDPR), and subject to the cold-start problem for new medications. Content-based filtering allows us to map patient conditions and reported symptoms directly into pharmacological indications and patient-reported satisfaction attributes without requiring cross-patient identity tracking.

### 2. Why is safety screening decoupled from recommendation scoring?
**Answer**: If safety were incorporated as a weighted numerical penalty in the recommendation scoring formula (e.g., $Score = w_1 Match + w_2 Sentiment - w_3 SafetyPenalty$), a medication with exceptionally high patient review ratings could mathematically overcome the safety penalty. In medicine, safety constraints (such as anaphylactic allergies or fatal drug interactions) are non-negotiable hard constraints. Decoupling ensures that high statistical scores never override clinical safety exclusions.

### 3. What does `NO_KNOWN_CONFLICT` mean, and why did you not use `SAFE`?
**Answer**: In clinical pharmacology, no drug is universally "safe" for all patients under all physiological circumstances. `NO_KNOWN_CONFLICT` accurately states that no matching rule was triggered in our local SQLite safety tables. Labeling a drug as `SAFE` would create a false clinical guarantee and violate medical ethics.

### 4. Why did you use rating-derived proxy supervision instead of manual medical annotation?
**Answer**: Annotating hundreds of thousands of clinical reviews by licensed pharmacologists is cost-prohibitive. The standard academic approach in biomedical NLP (Gräßer et al., 2018) uses numerical ratings ($1\text{--}10$) provided by patients as proxy ground truth ($\ge 7$ Positive, $5\text{--}6$ Neutral, $\le 4$ Negative). This reflects patient-reported satisfaction and tolerability, which we explicitly distinguish from clinical efficacy.

### 5. Why did you select TF-IDF + Logistic Regression over BioBERT or Large Language Models?
**Answer**: For our production prototype, TF-IDF + class-weighted Logistic Regression provides four key advantages:
1. **Deterministic attributions**: Exact feature coefficient inspection for explainability.
2. **Sub-millisecond inference**: Inference takes $<50\text{ms}$ on standard CPU hardware without GPU requirements.
3. **Zero stochastic hallucination**: Linear models cannot hallucinate nonexistent safety facts.
4. **Empirical accuracy**: $80.23\%$ accuracy on 53,200 holdout test samples.

### 6. How does your system prevent duplicate drug-drug interaction rules in SQLite?
**Answer**: We enforce an unordered pair foreign-key constraint: `drug_a_id < drug_b_id`. Whenever an interaction check is queried between medication $A$ and medication $B$, the system sorts the two IDs into $(\min(A, B), \max(A, B))$ before querying SQLite. This guarantees that $A+B$ and $B+A$ always resolve to the exact same canonical database record with zero duplicate entries.

### 7. Why was gender excluded from the patient profile?
**Answer**: Analysis of the Drugs.com review corpus and clinical pharmacology literature revealed that conditioning statistical drug recommendations on gender risks encoding historical prescribing biases rather than physiological indicators. Unless a specific condition is biologically sex-restricted, clinical dosage and safety primarily depend on age, renal function, active medications, and allergies.

### 8. What happens when a user enters an unknown condition or disease?
**Answer**: The system's condition matcher uses multi-stage resolution: exact match, alias mapping (`CONDITION_ALIASES`), and substring search. If the condition does not exist in the catalog, the system safely returns `recommended_drugs: []` and `filtered_drugs: []` with an informative message rather than crashing or fabricating hallucinations.

### 9. How does the system handle class imbalance during training?
**Answer**: The review dataset exhibits a natural positive skew ($65.9\%$ Positive, $25.1\%$ Negative, $9.0\%$ Neutral). We employed `class_weight='balanced'` in scikit-learn's `LogisticRegression`, which automatically weights classes inversely proportional to their frequencies. This boosted the Neutral class recall to $66.0\%$ and Negative class recall to $79.7\%$.

### 10. How are the natural language explanations generated?
**Answer**: Explanations are generated deterministically by `ExplanationService` through rule-based template decomposition. For recommended drugs, it reports exact percentage contributions for condition match, profile similarity, and sentiment probability. For filtered drugs, it cites the exact violated rule (e.g., `ALLERGY_CONFLICT_AND_DRUG_INTERACTION`), affected substances, and the FDA label clinical rationale.
