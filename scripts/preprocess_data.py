"""
Reproducible data preprocessing and SQLite Layer 1 database seeding pipeline.
"""

import os
import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Add backend directory to sys.path to import application modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.ml.preprocessing import (
    clean_review_text,
    decode_html_entities,
    is_valid_condition,
    normalize_condition_name,
    normalize_drug_name,
    get_sentiment_proxy_label,
    get_sentiment_proxy_int,
)
from app.db.database import init_db


def find_raw_file(raw_dir: Path, base_name: str) -> Path:
    """Finds raw file with .csv or .tsv extension."""
    for ext in [".csv", ".tsv", ".CSV", ".TSV"]:
        p = raw_dir / f"{base_name}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"Could not find {base_name} (.csv or .tsv) in {raw_dir}")


def preprocess_dataframe(df: pd.DataFrame, split_name: str) -> tuple[pd.DataFrame, dict]:
    """
    Cleans and preprocesses a raw drug review DataFrame.
    """
    raw_count = len(df)
    stats = {
        "raw_count": raw_count,
        "missing_condition": 0,
        "html_artifact_condition": 0,
        "empty_review": 0,
        "cleaned_count": 0,
    }

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    # Track missing condition
    stats["missing_condition"] = int(df["condition"].isna().sum())

    # Filter valid conditions
    valid_mask = df["condition"].apply(is_valid_condition)
    stats["html_artifact_condition"] = int((~valid_mask & df["condition"].notna()).sum())
    df_clean = df[valid_mask].copy()

    # Clean text columns
    df_clean["drugName"] = df_clean["drugName"].apply(normalize_drug_name)
    df_clean["condition"] = df_clean["condition"].apply(normalize_condition_name)
    df_clean["review_raw"] = df_clean["review"].copy()  # Preserve original review
    df_clean["review"] = df_clean["review"].apply(clean_review_text)

    # Filter empty reviews
    non_empty_mask = df_clean["review"].str.len() > 0
    stats["empty_review"] = int((~non_empty_mask).sum())
    df_clean = df_clean[non_empty_mask].copy()

    # Generate rating-derived proxy sentiment labels
    df_clean["rating"] = pd.to_numeric(df_clean["rating"], errors="coerce").fillna(0.0)
    df_clean["sentiment_label"] = df_clean["rating"].apply(get_sentiment_proxy_label)
    df_clean["sentiment_int"] = df_clean["rating"].apply(get_sentiment_proxy_int)

    # Useful count conversion
    df_clean["usefulCount"] = pd.to_numeric(df_clean["usefulCount"], errors="coerce").fillna(0).astype(int)

    stats["cleaned_count"] = len(df_clean)
    stats["removed_count"] = raw_count - len(df_clean)

    return df_clean, stats


def seed_sqlite_database(df_combined: pd.DataFrame, db_path: Path):
    """
    Populates SQLite Layer 1 tables (drugs, conditions, drug_conditions) idempotently.
    """
    conn = init_db(db_path)
    cursor = conn.cursor()

    # Begin transaction
    cursor.execute("BEGIN TRANSACTION;")

    # 1. Clear existing Layer 1 data to ensure idempotence
    cursor.execute("DELETE FROM drug_conditions;")
    cursor.execute("DELETE FROM conditions;")
    cursor.execute("DELETE FROM drugs;")

    # 2. Aggregate drug-level statistics
    drug_stats = (
        df_combined.groupby("drugName")
        .agg(
            total_reviews=("uniqueID", "count"),
            avg_rating=("rating", "mean"),
            positive_reviews=("sentiment_label", lambda s: (s == "Positive").sum()),
        )
        .reset_index()
    )
    drug_stats["avg_rating"] = drug_stats["avg_rating"].round(2)
    drug_stats["positive_sentiment_ratio"] = (
        drug_stats["positive_reviews"] / drug_stats["total_reviews"]
    ).round(4)

    # Insert drugs
    for _, row in drug_stats.iterrows():
        cursor.execute(
            """
            INSERT INTO drugs (name, generic_name, drug_class, description, avg_rating, total_reviews, positive_sentiment_ratio)
            VALUES (?, NULL, 'Not specified', NULL, ?, ?, ?)
            """,
            (
                row["drugName"],
                float(row["avg_rating"]),
                int(row["total_reviews"]),
                float(row["positive_sentiment_ratio"]),
            ),
        )

    # Fetch mapping of drugName -> drug_id
    cursor.execute("SELECT name, drug_id FROM drugs;")
    drug_id_map = dict(cursor.fetchall())

    # 3. Insert unique conditions
    unique_conditions = sorted(df_combined["condition"].unique())
    for cond in unique_conditions:
        cursor.execute(
            """
            INSERT INTO conditions (name, category)
            VALUES (?, 'General')
            """,
            (cond,),
        )

    # Fetch mapping of condition -> condition_id
    cursor.execute("SELECT name, condition_id FROM conditions;")
    condition_id_map = dict(cursor.fetchall())

    # 4. Insert drug_conditions mappings
    dc_stats = (
        df_combined.groupby(["drugName", "condition"])
        .agg(
            review_count=("uniqueID", "count"),
            avg_rating=("rating", "mean"),
        )
        .reset_index()
    )
    dc_stats["avg_rating"] = dc_stats["avg_rating"].round(2)

    for _, row in dc_stats.iterrows():
        drug_id = drug_id_map[row["drugName"]]
        condition_id = condition_id_map[row["condition"]]
        cursor.execute(
            """
            INSERT INTO drug_conditions (drug_id, condition_id, review_count, avg_rating)
            VALUES (?, ?, ?, ?)
            """,
            (
                drug_id,
                condition_id,
                int(row["review_count"]),
                float(row["avg_rating"]),
            ),
        )

    conn.commit()
    conn.close()


def run_pipeline():
    raw_dir = PROJECT_ROOT / "data" / "raw"
    processed_dir = PROJECT_ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    db_path = processed_dir / "drug_system.db"

    print("=" * 60)
    print("PHASE 2A: DATASET PREPROCESSING & DATABASE SEEDING")
    print("=" * 60)

    train_file = find_raw_file(raw_dir, "drugsComTrain_raw")
    test_file = find_raw_file(raw_dir, "drugsComTest_raw")

    print(f"Detected Train File: {train_file.name} ({train_file.stat().st_size:,} bytes)")
    print(f"Detected Test File:  {test_file.name} ({test_file.stat().st_size:,} bytes)")

    # Read raw datasets
    df_raw_train = pd.read_csv(train_file)
    df_raw_test = pd.read_csv(test_file)

    # Preprocess splits
    df_clean_train, train_stats = preprocess_dataframe(df_raw_train, "train")
    df_clean_test, test_stats = preprocess_dataframe(df_raw_test, "test")

    # Combine for global statistics and database seeding
    df_combined = pd.concat([df_clean_train, df_clean_test], ignore_index=True)

    # Save cleaned splits
    clean_train_path = processed_dir / "drugs_cleaned_train.csv"
    clean_test_path = processed_dir / "drugs_cleaned_test.csv"
    clean_combined_path = processed_dir / "drugs_cleaned_combined.csv"

    df_clean_train.to_csv(clean_train_path, index=False)
    df_clean_test.to_csv(clean_test_path, index=False)
    df_combined.to_csv(clean_combined_path, index=False)

    print("\nSaved Processed Data Files:")
    print(f"  - {clean_train_path.name} ({len(df_clean_train):,} rows)")
    print(f"  - {clean_test_path.name} ({len(df_clean_test):,} rows)")
    print(f"  - {clean_combined_path.name} ({len(df_combined):,} rows)")

    # Seed Database
    print("\nSeeding SQLite Database at:", db_path)
    seed_sqlite_database(df_combined, db_path)

    # Validation Queries
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM drugs;")
    total_drugs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM conditions;")
    total_conditions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM drug_conditions;")
    total_drug_conditions = cursor.fetchone()[0]

    # Verify foreign key integrity
    cursor.execute(
        """
        SELECT COUNT(*) FROM drug_conditions dc
        LEFT JOIN drugs d ON dc.drug_id = d.drug_id
        LEFT JOIN conditions c ON dc.condition_id = c.condition_id
        WHERE d.drug_id IS NULL OR c.condition_id IS NULL;
        """
    )
    orphan_records = cursor.fetchone()[0]

    conn.close()

    # Sentiment distribution
    sentiment_dist = df_combined["sentiment_label"].value_counts().to_dict()

    # Top conditions
    top_conditions = df_combined["condition"].value_counts().head(10).to_dict()

    # Top drugs
    top_drugs = df_combined["drugName"].value_counts().head(10).to_dict()

    print("\n" + "=" * 60)
    print("ACTUAL OBSERVED DATASET METRICS")
    print("=" * 60)
    print(f"Raw Train Rows:           {train_stats['raw_count']:,}")
    print(f"Raw Test Rows:            {test_stats['raw_count']:,}")
    print(f"Raw Total Rows:           {train_stats['raw_count'] + test_stats['raw_count']:,}")
    print(f"Cleaned Train Rows:       {train_stats['cleaned_count']:,}")
    print(f"Cleaned Test Rows:        {test_stats['cleaned_count']:,}")
    print(f"Cleaned Total Rows:       {len(df_combined):,}")
    print(f"Removed Rows:             {train_stats['removed_count'] + test_stats['removed_count']:,} "
          f"({train_stats['missing_condition'] + test_stats['missing_condition']} missing condition, "
          f"{train_stats['html_artifact_condition'] + test_stats['html_artifact_condition']} html artifact condition)")
    print(f"Unique Drugs (Seeded):    {total_drugs:,}")
    print(f"Unique Conditions (Seeded): {total_conditions:,}")
    print(f"Drug-Condition Mappings:  {total_drug_conditions:,}")
    print(f"Foreign Key Orphans:      {orphan_records} (0 expected)")
    print("\nRating-Derived Sentiment Proxy Label Distribution:")
    for k, v in sentiment_dist.items():
        pct = (v / len(df_combined)) * 100
        print(f"  - {k:10s}: {v:,} ({pct:.2f}%)")
    print("\nTop 5 Conditions:")
    for cond, cnt in list(top_conditions.items())[:5]:
        print(f"  - {cond:25s}: {cnt:,} reviews")
    print("\nTop 5 Drugs:")
    for drug, cnt in list(top_drugs.items())[:5]:
        print(f"  - {drug:25s}: {cnt:,} reviews")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
