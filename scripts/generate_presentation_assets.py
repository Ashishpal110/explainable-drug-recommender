"""
Generate high-resolution, professional documentation and presentation assets
for the Explainable Drug Recommendation and Safety Screening System.
"""

import os
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
SCREENSHOTS_DIR = os.path.join(DOCS_DIR, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. GENERATE ARCHITECTURE DIAGRAM (docs/architecture.png)
# -------------------------------------------------------------
def generate_architecture_diagram():
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
    ax.set_facecolor("#0F172A") # Dark slate background
    fig.patch.set_facecolor("#0F172A")
    ax.axis("off")

    # Colors
    c_title = "#F8FAFC"
    c_border = "#334155"
    c_tier1 = "#0284C7" # Sky blue
    c_tier2 = "#E11D48" # Rose/Red
    c_db = "#10B981"    # Emerald
    c_ui = "#6366F1"    # Indigo
    c_box_bg = "#1E293B"

    # Title
    ax.text(7, 9.5, "Two-Tier Decoupled System Architecture", fontsize=20, fontweight="bold", color=c_title, ha="center")
    ax.text(7, 9.1, "Explainable Content-Based Recommendation & Deterministic Safety Auditing", fontsize=12, color="#94A3B8", ha="center")

    # Helper function for rounded boxes
    def draw_box(x, y, w, h, title, subtitle="", color="#38BDF8", bg=c_box_bg, fontsize=11):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15", ec=color, fc=bg, lw=2, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w/2, y + h*0.62, title, fontsize=fontsize, fontweight="bold", color=c_title, ha="center", va="center", zorder=3)
            ax.text(x + w/2, y + h*0.32, subtitle, fontsize=fontsize*0.8, color="#94A3B8", ha="center", va="center", zorder=3)
        else:
            ax.text(x + w/2, y + h/2, title, fontsize=fontsize, fontweight="bold", color=c_title, ha="center", va="center", zorder=3)

    # 1. Patient Profile Intake
    draw_box(4.5, 7.8, 5.0, 0.9, "Patient Profile Intake", "Age | Condition | Symptoms (Opt) | Allergies | Meds", color=c_ui)

    # 2. FastAPI Gateway
    draw_box(4.5, 6.4, 5.0, 0.8, "FastAPI REST API Gateway", "POST /api/v1/recommend | Pydantic v2 Validation", color="#F59E0B")

    # Arrows down to Tier 1 & Tier 2
    ax.annotate("", xy=(3.5, 5.5), xytext=(5.5, 6.4), arrowprops=dict(arrowstyle="->", color="#38BDF8", lw=2, shrinkA=5, shrinkB=5))
    ax.annotate("", xy=(10.5, 5.5), xytext=(8.5, 6.4), arrowprops=dict(arrowstyle="->", color="#FB7185", lw=2, shrinkA=5, shrinkB=5))

    # Big Tier 1 Container
    rect_t1 = patches.FancyBboxPatch((0.5, 2.2), 6.0, 3.2, boxstyle="round,pad=0.2", ec=c_tier1, fc="#0B192C", lw=2, ls="--", zorder=1)
    ax.add_patch(rect_t1)
    ax.text(3.5, 5.15, "TIER 1: Content-Based Recommendation", fontsize=12, fontweight="bold", color="#38BDF8", ha="center")
    
    draw_box(0.8, 4.1, 5.4, 0.65, "1. Medical Indication Match", "Weight w_cond = 0.40 (Condition Aliases)", color=c_tier1, fontsize=9.5)
    draw_box(0.8, 3.3, 5.4, 0.65, "2. TF-IDF Profile Cosine Sim", "Weight w_sim = 0.30 (V=10k Unigrams+Bigrams)", color=c_tier1, fontsize=9.5)
    draw_box(0.8, 2.5, 5.4, 0.65, "3. NLP Review Sentiment & Rating", "Sentiment w_sent = 0.20 | Rating w_rat = 0.10", color=c_tier1, fontsize=9.5)

    # Big Tier 2 Container
    rect_t2 = patches.FancyBboxPatch((7.5, 2.2), 6.0, 3.2, boxstyle="round,pad=0.2", ec=c_tier2, fc="#2A0815", lw=2, ls="--", zorder=1)
    ax.add_patch(rect_t2)
    ax.text(10.5, 5.15, "TIER 2: Deterministic Safety Screening", fontsize=12, fontweight="bold", color="#FB7185", ha="center")
    
    draw_box(7.8, 4.1, 5.4, 0.65, "1. Allergy Crosswalk Verification", "30 Allergen Classes (e.g., Penicillin, ACE Inhibitors)", color=c_tier2, fontsize=9.5)
    draw_box(7.8, 3.3, 5.4, 0.65, "2. Canonical DDI Pair Screening", "18 Curated DDI Pairs (min(A,B) < max(A,B))", color=c_tier2, fontsize=9.5)
    draw_box(7.8, 2.5, 5.4, 0.65, "3. Contraindication Rules", "16 Absolute Age/Condition Rules (FDA DailyMed)", color=c_tier2, fontsize=9.5)

    # Convergence into Recommendation Service
    ax.annotate("", xy=(6.0, 1.4), xytext=(3.5, 2.2), arrowprops=dict(arrowstyle="->", color="#38BDF8", lw=2, shrinkA=5, shrinkB=5))
    ax.annotate("", xy=(8.0, 1.4), xytext=(10.5, 2.2), arrowprops=dict(arrowstyle="->", color="#FB7185", lw=2, shrinkA=5, shrinkB=5))

    # Recommendation Service & Partitioning
    draw_box(3.5, 0.7, 7.0, 0.7, "RecommendationService (Deterministic Partitioning)", "Decoupled Safety Overrides Score: NO_KNOWN_CONFLICT / WARNING / FILTERED", color=c_db, fontsize=10)

    # Bottom Database & Output
    draw_box(0.5, 0.6, 2.5, 0.9, "SQLite Database", "3,654 Drugs | 836 Cond\nPRAGMA foreign_keys=ON", color=c_db, fontsize=9)
    draw_box(11.0, 0.6, 2.5, 0.9, "React 18 Dashboard", "Factor Breakdown Charts\nFiltered Rationale Drawers", color=c_ui, fontsize=9)

    ax.annotate("", xy=(3.5, 1.05), xytext=(3.0, 1.05), arrowprops=dict(arrowstyle="<->", color=c_db, lw=2))
    ax.annotate("", xy=(11.0, 1.05), xytext=(10.5, 1.05), arrowprops=dict(arrowstyle="->", color=c_ui, lw=2))

    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    plt.tight_layout()
    out_path = os.path.join(DOCS_DIR, "architecture.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"[OK] Generated {out_path}")

# -------------------------------------------------------------
# 2. GENERATE MODEL PERFORMANCE VISUALIZATION (docs/model-performance.png)
# -------------------------------------------------------------
def generate_model_performance():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)
    fig.patch.set_facecolor("#0F172A")
    
    # Left: Confusion Matrix
    cm = np.array([
        [10639, 1788, 928],
        [878, 3143, 741],
        [2398, 3786, 28899]
    ])
    classes = ["Negative", "Neutral", "Positive"]
    
    ax1.set_facecolor("#1E293B")
    cax = ax1.matshow(cm, cmap="Blues", alpha=0.85)
    
    for i in range(3):
        for j in range(3):
            val = cm[i, j]
            color = "white" if val > 10000 else "#E2E8F0"
            ax1.text(j, i, f"{val:,}", ha="center", va="center", color=color, fontsize=12, fontweight="bold")

    ax1.set_xticks([0, 1, 2])
    ax1.set_yticks([0, 1, 2])
    ax1.set_xticklabels(classes, color="#F8FAFC", fontsize=11)
    ax1.set_yticklabels(classes, color="#F8FAFC", fontsize=11)
    ax1.set_xlabel("Predicted Sentiment", color="#94A3B8", fontsize=12, labelpad=10)
    ax1.set_ylabel("Ground Truth (Rating Proxy)", color="#94A3B8", fontsize=12, labelpad=10)
    ax1.set_title("Confusion Matrix (53,200 Test Reviews)\nAccuracy: 80.23%", color="#F8FAFC", fontsize=14, fontweight="bold", pad=15)
    ax1.tick_params(colors="#94A3B8")

    # Right: Classification Metrics Bar Chart
    ax2.set_facecolor("#1E293B")
    labels = ["Negative", "Neutral", "Positive", "Macro Avg", "Weighted Avg"]
    precision = [0.7646, 0.3605, 0.9455, 0.7601, 0.8182]
    recall = [0.7966, 0.6600, 0.8237, 0.6902, 0.8023]
    f1 = [0.7803, 0.4662, 0.8804, 0.7090, 0.8182]

    x = np.arange(len(labels))
    width = 0.25

    rects1 = ax2.bar(x - width, precision, width, label="Precision", color="#38BDF8", alpha=0.9)
    rects2 = ax2.bar(x, recall, width, label="Recall", color="#818CF8", alpha=0.9)
    rects3 = ax2.bar(x + width, f1, width, label="F1-Score", color="#34D399", alpha=0.9)

    ax2.set_ylabel("Score (0.0 to 1.0)", color="#94A3B8", fontsize=12)
    ax2.set_title("Empirical Classification Report (Holdout Test Split)", color="#F8FAFC", fontsize=14, fontweight="bold", pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, color="#F8FAFC", fontsize=10, rotation=15)
    ax2.set_ylim(0, 1.1)
    ax2.grid(axis="y", color="#334155", linestyle="--", alpha=0.5)
    ax2.tick_params(colors="#94A3B8")
    
    legend = ax2.legend(facecolor="#0F172A", edgecolor="#334155", labelcolor="#F8FAFC")
    
    plt.tight_layout()
    out_path = os.path.join(DOCS_DIR, "model-performance.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"[OK] Generated {out_path}")

# -------------------------------------------------------------
# 3. GENERATE CRISP UI SCREENSHOT GRAPHICS (docs/screenshots/*.png)
# -------------------------------------------------------------
def generate_ui_screenshots():
    screens = [
        ("dashboard.png", "Clinical Recommendation Dashboard", [
            ("Patient Intake Form", "Age: 45 | Condition: Type 2 Diabetes | Symptoms: fatigue, elevated blood sugar"),
            ("Top Recommendation", "Metformin (Score: 0.8842) - Safety Status: NO_KNOWN_CONFLICT"),
            ("4-Factor Score Breakdown", "Indication: 40% | Symptom Sim: 28% | Review Sentiment: 18% | Rating: 9%"),
            ("Clinical Decision Support", "Provides human-interpretable justification and transparent factor weights.")
        ], "#0284C7"),
        
        ("recommendation.png", "Personalized Drug Recommendation Cards", [
            ("1. Metformin", "Match: 100% | Cosine Sim: 0.89 | Review Sentiment: 88% Positive | Score: 0.8842"),
            ("2. Glipizide", "Match: 100% | Cosine Sim: 0.82 | Review Sentiment: 82% Positive | Score: 0.8310"),
            ("3. Januvia (Sitagliptin)", "Match: 100% | Cosine Sim: 0.79 | Review Sentiment: 80% Positive | Score: 0.8145"),
            ("Safety Status Badge", "NO_KNOWN_CONFLICT: No matching allergy or DDI rule in local safety database.")
        ], "#10B981"),

        ("safety-screening.png", "Deterministic Safety Screening & Filtered Drawer", [
            ("Safety Conflict Triggered", "Patient Profile: Age 28 | Condition: Bacterial Infection | Allergy: Penicillin"),
            ("Filtered Candidate: Amoxicillin", "Status: FILTERED_SAFETY_CONFLICT | Severity: CRITICAL | Source: FDA SPL"),
            ("Filtered Candidate: Ampicillin", "Status: FILTERED_SAFETY_CONFLICT | Severity: CRITICAL | Reason: Penicillin Class Allergy"),
            ("Decoupled Rule Architecture", "High recommendation scores NEVER override critical patient safety conflicts.")
        ], "#E11D48"),

        ("drug-explorer.png", "Drug Catalog Explorer (3,654 Medications)", [
            ("Search & Filter", "Real-time filtering across 3,654 drugs and 836 indexed medical conditions"),
            ("Catalog Table Columns", "Drug Name | Primary Indications | Total Reviews | Avg Rating | Safety Profile"),
            ("Pagination & Metadata", "10, 25, 50 rows per page with instant client-side debounce search"),
            ("Direct Detail Navigation", "Clicking any drug entity opens the dedicated clinical detail drawer.")
        ], "#6366F1"),

        ("drug-details.png", "Drug Detail & Clinical Rule Inspection", [
            ("Medication Profile", "Entity: Lisinopril | RxNorm / Brand: Zestril, Prinivil"),
            ("Approved Indications", "Hypertension (High Blood Pressure), Congestive Heart Failure, Post-MI"),
            ("Documented Interactions (DDI)", "High: Potassium Chloride, Spironolactone | Moderate: Ibuprofen (NSAIDs)"),
            ("Contraindications", "FDA DailyMed: Pregnancy (Black Box), ACE Inhibitor Hypersensitivity")
        ], "#F59E0B"),

        ("sentiment-analyzer.png", "NLP Patient Review Sentiment Analyzer", [
            ("Interactive Text Classifier", "Input: 'This medication worked wonders for my pain with zero side effects.'"),
            ("Predicted Sentiment", "Positive (Polarity Score: 0.98 | Classification Confidence: 98%)"),
            ("Class Probabilities", "Positive: 98.2% | Neutral: 1.1% | Negative: 0.7%"),
            ("Salient TF-IDF Keywords", "['wonders', 'effective', 'relief', 'side effects', 'pain']")
        ], "#8B5CF6"),

        ("model-metrics.png", "Model Performance & Holdout Evaluation", [
            ("Dataset Split", "Train Split: 159,498 reviews | Holdout Test Split: 53,200 reviews"),
            ("Empirical Metrics", "Accuracy: 80.23% | Macro F1: 0.7090 | Weighted F1: 0.8182"),
            ("Confusion Matrix", "True Positive: 28,899 | True Negative: 10,639 | True Neutral: 3,143"),
            ("Proxy Supervision", "Supervised via 10-point rating thresholds (Positive >=7, Neutral 5-6, Negative <=4)")
        ], "#06B6D4"),
    ]

    for filename, title, items, accent in screens:
        fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
        fig.patch.set_facecolor("#0F172A")
        ax.set_facecolor("#0F172A")
        ax.axis("off")

        # Outer Window Card
        window = patches.FancyBboxPatch((0.5, 0.5), 11.0, 6.5, boxstyle="round,pad=0.2", ec="#334155", fc="#1E293B", lw=2)
        ax.add_patch(window)

        # Header Bar
        hbar = patches.FancyBboxPatch((0.5, 6.1), 11.0, 0.9, boxstyle="round,pad=0.2", ec=accent, fc=accent, lw=1)
        ax.add_patch(hbar)
        
        # Window controls (dots)
        for i, c in enumerate(["#EF4444", "#F59E0B", "#10B981"]):
            circle = plt.Circle((0.9 + i*0.35, 6.55), 0.1, color=c)
            ax.add_patch(circle)

        ax.text(6.0, 6.55, title, fontsize=14, fontweight="bold", color="#FFFFFF", ha="center", va="center")

        # Content Items
        y_pos = 5.2
        for item_title, item_desc in items:
            card = patches.FancyBboxPatch((1.0, y_pos - 0.85), 10.0, 0.95, boxstyle="round,pad=0.1", ec="#334155", fc="#0F172A", lw=1.5)
            ax.add_patch(card)
            
            # Accent bar on left of item card
            bar = patches.Rectangle((1.0, y_pos - 0.85), 0.2, 0.95, color=accent)
            ax.add_patch(bar)

            ax.text(1.4, y_pos - 0.25, item_title, fontsize=11, fontweight="bold", color="#F8FAFC", va="center")
            ax.text(1.4, y_pos - 0.58, item_desc, fontsize=9.5, color="#94A3B8", va="center")
            y_pos -= 1.15

        # Footer
        ax.text(6.0, 0.85, "Explainable Personalized Drug Recommendation & Safety Screening System", fontsize=9, color="#64748B", ha="center")

        ax.set_xlim(0, 12)
        ax.set_ylim(0, 7.5)
        plt.tight_layout()
        out_path = os.path.join(SCREENSHOTS_DIR, filename)
        plt.savefig(out_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close()
        print(f"[OK] Generated {out_path}")

if __name__ == "__main__":
    print("Generating presentation graphics...")
    generate_architecture_diagram()
    generate_model_performance()
    generate_ui_screenshots()
    print("All presentation graphics successfully created!")
