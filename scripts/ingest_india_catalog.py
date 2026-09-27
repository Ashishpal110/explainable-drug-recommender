"""
Deterministic, idempotent ingestion and normalization pipeline for the Indian Pharmaceutical Dataset.
Parses brand names, dosage forms, multi-salt compositions, active ingredient strengths,
and maps authoritative clinical indications (NFI / CDSCO).
"""

import sys
import io
import json
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

# Add project root and backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from app.data.normalization import (
    extract_brand_and_dosage_form,
    parse_drug_compositions,
    normalize_manufacturer_name,
    get_canonical_ingredient_name,
)
from app.db.database import init_db

# File paths
RAW_CSV_PATH = PROJECT_ROOT / "data" / "raw" / "india" / "medicine.csv"
DB_PATH = PROJECT_ROOT / "data" / "processed" / "drug_system.db"
CLINICAL_INDICATIONS_PATH = PROJECT_ROOT / "data" / "curated" / "clinical_indications_in.json"
SAFETY_JSON_PATH = PROJECT_ROOT / "data" / "safety" / "verified_safety_rules.json"


def ingest_indian_pharmaceutical_catalog(
    raw_csv: Path = RAW_CSV_PATH,
    db_path: Path = DB_PATH,
    indications_json: Path = CLINICAL_INDICATIONS_PATH,
    limit: int | None = None
) -> Dict[str, Any]:
    """
    Executes the ingestion, normalization, and database population for Indian medicines.
    """
    print("=" * 70)
    print("STEP 3: INGESTING INDIAN PHARMACEUTICAL DATA LAYER")
    print("=" * 70)

    if not raw_csv.exists():
        raise FileNotFoundError(f"Raw Indian medicine dataset not found at {raw_csv}")

    if not indications_json.exists():
        raise FileNotFoundError(f"Clinical indications file not found at {indications_json}")

    # 1. Load Clinical Indications Mapping
    with open(indications_json, "r", encoding="utf-8") as f:
        indications_data = json.load(f)

    # Build canonical_ingredient -> list of indication objects mapping
    ingredient_to_indications = {}
    for entry in indications_data.get("indications", []):
        canon_name = entry["canonical_ingredient"].strip().lower()
        ingredient_to_indications[canon_name] = {
            "drug_class": entry.get("drug_class", "Not specified"),
            "conditions": entry.get("conditions", []),
            "evidence_source": entry.get("evidence_source", "National Formulary of India (NFI 2021)"),
            "evidence_reference": entry.get("evidence_reference", "")
        }

    print(f"Loaded {len(ingredient_to_indications)} authoritative clinical indication profiles.")

    # 2. Read and Validate Raw Dataset
    print(f"Reading raw CSV: {raw_csv} ...")
    df_raw = pd.read_csv(raw_csv)
    raw_count = len(df_raw)
    print(f"Total raw records: {raw_count:,}")

    required_cols = ["id", "name", "price(₹)", "Is_discontinued", "manufacturer_name", "short_composition1"]
    for col in required_cols:
        if col not in df_raw.columns:
            raise ValueError(f"Required column '{col}' missing from raw CSV.")

    # 3. Filter Discontinued & Duplicates
    discontinued_count = int(df_raw["Is_discontinued"].sum())
    df_active = df_raw[df_raw["Is_discontinued"] == False].copy()
    active_count = len(df_active)
    print(f"Active (non-discontinued) records: {active_count:,} (Filtered {discontinued_count:,} discontinued)")

    # Deduplicate on name + short_composition1 + manufacturer_name if exact duplicate
    initial_active = len(df_active)
    df_active = df_active.drop_duplicates(subset=["name", "short_composition1", "manufacturer_name"])
    duplicate_count = initial_active - len(df_active)
    print(f"Duplicates removed: {duplicate_count:,}")

    if limit:
        df_active = df_active.head(limit)
        print(f"Limiting to first {limit} records for testing...")

    # 4. Initialize Database
    conn = init_db(db_path)
    cursor = conn.cursor()

    # Track Normalization Statistics
    stats = {
        "total_raw_records": raw_count,
        "discontinued_filtered": discontinued_count,
        "duplicate_records_removed": duplicate_count,
        "active_records_processed": len(df_active),
        "successful_composition_parses": 0,
        "partial_composition_parses": 0,
        "drugs_inserted": 0,
        "ingredients_inserted": 0,
        "conditions_created": 0,
        "drug_conditions_linked": 0,
        "safety_crosswalk_rules_seeded": 0,
        "unique_manufacturers": int(df_active["manufacturer_name"].nunique()),
    }

    # Ensure canonical conditions exist in conditions table
    cursor.execute("SELECT name, condition_id FROM conditions;")
    condition_map = {row[0].lower(): row[1] for row in cursor.fetchall()}

    for ing_info in ingredient_to_indications.values():
        for cond in ing_info["conditions"]:
            cond_name = cond["name"].strip()
            if cond_name.lower() not in condition_map:
                cursor.execute(
                    "INSERT OR IGNORE INTO conditions (name, category) VALUES (?, 'General');",
                    (cond_name,)
                )
                cursor.execute("SELECT condition_id FROM conditions WHERE name = ?;", (cond_name,))
                row = cursor.fetchone()
                if row:
                    condition_map[cond_name.lower()] = row[0]
                    stats["conditions_created"] += 1

    conn.commit()

    # Begin Database Ingestion Transaction
    cursor.execute("BEGIN TRANSACTION;")

    # To ensure safety and idempotence, clear existing drug_ingredients
    cursor.execute("DELETE FROM drug_ingredients;")

    print("Parsing records and preparing batch data...")

    drugs_batch = []
    parsed_records = []

    for idx, row in df_active.iterrows():
        raw_name = str(row["name"]).strip()
        raw_comp1 = str(row["short_composition1"]) if pd.notna(row["short_composition1"]) else None
        raw_comp2 = str(row["short_composition2"]) if pd.notna(row["short_composition2"]) else None
        raw_price = float(row["price(₹)"]) if pd.notna(row["price(₹)"]) else 0.0
        raw_mfr = str(row["manufacturer_name"]) if pd.notna(row["manufacturer_name"]) else "Unknown Manufacturer"
        pack_size = str(row["pack_size_label"]) if pd.notna(row["pack_size_label"]) else None

        # Brand normalization & dosage form extraction
        brand_name, dosage_form = extract_brand_and_dosage_form(raw_name)
        mfr_name = normalize_manufacturer_name(raw_mfr)

        # Composition parsing
        ingredients = parse_drug_compositions(raw_comp1, raw_comp2)
        if ingredients:
            stats["successful_composition_parses"] += 1
        else:
            stats["partial_composition_parses"] += 1

        comp_parts = [ing["raw"] for ing in ingredients]
        full_comp = " + ".join(comp_parts) if comp_parts else (raw_comp1 or "Not specified")

        generic_names = [ing["canonical_name"] for ing in ingredients if ing["canonical_name"]]
        generic_name_str = " + ".join(generic_names) if generic_names else None

        drug_class = "Not specified"
        matched_indications = []
        for ing in ingredients:
            c_name = ing["canonical_name"]
            if c_name in ingredient_to_indications:
                drug_class = ingredient_to_indications[c_name]["drug_class"]
                for cond_entry in ingredient_to_indications[c_name]["conditions"]:
                    matched_indications.append({
                        "condition_name": cond_entry["name"],
                        "indication_type": cond_entry["indication_type"],
                        "evidence_source": ingredient_to_indications[c_name]["evidence_source"]
                    })

        drugs_batch.append((
            raw_name, generic_name_str, full_comp, drug_class, mfr_name,
            raw_price, dosage_form, pack_size
        ))
        parsed_records.append((raw_name, ingredients, matched_indications))

    print(f"Executing batch insert for {len(drugs_batch):,} drugs...")
    cursor.executemany(
        """
        INSERT INTO drugs (
            name, generic_name, composition, drug_class, manufacturer,
            price_inr, dosage_form, pack_size, is_discontinued,
            avg_rating, total_reviews, positive_sentiment_ratio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0.0, 0, 0.0)
        ON CONFLICT(name) DO UPDATE SET
            generic_name = excluded.generic_name,
            composition = excluded.composition,
            drug_class = excluded.drug_class,
            manufacturer = excluded.manufacturer,
            price_inr = excluded.price_inr,
            dosage_form = excluded.dosage_form,
            pack_size = excluded.pack_size,
            is_discontinued = 0;
        """,
        drugs_batch
    )
    stats["drugs_inserted"] = len(drugs_batch)

    # Fetch updated drug_ids in bulk
    cursor.execute("SELECT name, drug_id FROM drugs;")
    drug_id_lookup = {row[0]: row[1] for row in cursor.fetchall()}

    ingredients_batch = []
    drug_conditions_batch = []

    for raw_name, ingredients, matched_indications in parsed_records:
        if raw_name not in drug_id_lookup:
            continue
        d_id = drug_id_lookup[raw_name]

        for ing in ingredients:
            ingredients_batch.append((
                d_id, ing["active_ingredient"], ing["strength_value"], ing["strength_unit"],
                ing["canonical_name"], "Indian Medicine Dataset"
            ))

        for ind in matched_indications:
            c_name_lower = ind["condition_name"].lower()
            if c_name_lower in condition_map:
                c_id = condition_map[c_name_lower]
                drug_conditions_batch.append((
                    d_id, c_id, ind["indication_type"], ind["evidence_source"]
                ))

    print(f"Executing batch insert for {len(ingredients_batch):,} ingredient records...")
    cursor.executemany(
        """
        INSERT INTO drug_ingredients (
            drug_id, active_ingredient, strength_value, strength_unit, canonical_name, source
        ) VALUES (?, ?, ?, ?, ?, ?);
        """,
        ingredients_batch
    )
    stats["ingredients_inserted"] = len(ingredients_batch)

    print(f"Executing batch insert for {len(drug_conditions_batch):,} drug condition links...")
    cursor.executemany(
        """
        INSERT OR REPLACE INTO drug_conditions (
            drug_id, condition_id, review_count, avg_rating, indication_type, evidence_source
        ) VALUES (?, ?, 0, 0.0, ?, ?);
        """,
        drug_conditions_batch
    )
    stats["drug_conditions_linked"] = len(drug_conditions_batch)

    # 5. Re-seed Verified Safety Rules linking canonical ingredients to Indian drugs
    if SAFETY_JSON_PATH.exists():
        with open(SAFETY_JSON_PATH, "r", encoding="utf-8") as f:
            safety_data = json.load(f)

        # Allergy crosswalk
        cursor.execute("DELETE FROM allergy_crosswalk;")
        cursor.execute("DELETE FROM drug_interactions;")
        cursor.execute("DELETE FROM contraindications;")

        # Map canonical ingredients to drug_ids
        cursor.execute("SELECT DISTINCT canonical_name, drug_id FROM drug_ingredients;")
        ing_to_drug_ids = {}
        for c_name, d_id in cursor.fetchall():
            ing_to_drug_ids.setdefault(c_name.lower(), []).append(d_id)

        # Also map drugs table name / generic_name
        cursor.execute("SELECT LOWER(name), LOWER(COALESCE(generic_name, '')), drug_id FROM drugs;")
        for name_l, gen_l, d_id in cursor.fetchall():
            ing_to_drug_ids.setdefault(name_l, []).append(d_id)
            for part in gen_l.split("+"):
                part_clean = part.strip()
                if part_clean:
                    ing_to_drug_ids.setdefault(part_clean, []).append(d_id)

        # Seed allergies
        allergy_count = 0
        for item in safety_data.get("allergies", []):
            drug_name_clean = get_canonical_ingredient_name(item["drug_name"])
            matching_ids = set(ing_to_drug_ids.get(drug_name_clean, []) + ing_to_drug_ids.get(item["drug_name"].strip().lower(), []))
            for target_id in matching_ids:
                cursor.execute(
                    """
                    INSERT INTO allergy_crosswalk (drug_id, allergen_class, reaction_severity, notes, source)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        target_id,
                        item["allergen_class"].strip(),
                        item.get("reaction_severity", "HIGH"),
                        item.get("notes"),
                        item["source"],
                    )
                )
                allergy_count += 1

        # Seed contraindications
        contra_count = 0
        for item in safety_data.get("contraindications", []):
            drug_name_clean = get_canonical_ingredient_name(item["drug_name"])
            matching_ids = set(ing_to_drug_ids.get(drug_name_clean, []) + ing_to_drug_ids.get(item["drug_name"].strip().lower(), []))
            for target_id in matching_ids:
                cursor.execute(
                    """
                    INSERT INTO contraindications (drug_id, contraindication_type, trigger_value, severity, reason, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        target_id,
                        item.get("contraindication_type", item.get("type", "CONDITION")).strip().upper(),
                        str(item["trigger_value"]).strip(),
                        item.get("severity", "CRITICAL").strip().upper(),
                        item.get("reason", "Contraindicated"),
                        item.get("source", "Clinical monograph"),
                    )
                )
                contra_count += 1

        # Seed DDIs
        ddi_count = 0
        seen_pairs = set()
        for item in safety_data.get("interactions", []):
            name_a_clean = get_canonical_ingredient_name(item["drug_a"])
            name_b_clean = get_canonical_ingredient_name(item["drug_b"])

            ids_a = set(ing_to_drug_ids.get(name_a_clean, []) + ing_to_drug_ids.get(item["drug_a"].strip().lower(), []))
            ids_b = set(ing_to_drug_ids.get(name_b_clean, []) + ing_to_drug_ids.get(item["drug_b"].strip().lower(), []))

            for id_a in ids_a:
                for id_b in ids_b:
                    if id_a == id_b:
                        continue
                    low_id, high_id = (id_a, id_b) if id_a < id_b else (id_b, id_a)
                    if (low_id, high_id) in seen_pairs:
                        continue
                    seen_pairs.add((low_id, high_id))

                    cursor.execute(
                        """
                        INSERT INTO drug_interactions (drug_a_id, drug_b_id, severity, interaction_mechanism, clinical_action, source)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            low_id,
                            high_id,
                            item.get("severity", "MODERATE").strip().upper(),
                            item.get("interaction_mechanism", item.get("mechanism", "Pharmacokinetic/dynamic interaction")),
                            item.get("clinical_action", "Monitor patient"),
                            item.get("source", "Clinical drug reference"),
                        )
                    )
                    ddi_count += 1

        stats["safety_crosswalk_rules_seeded"] = allergy_count + contra_count + ddi_count
        print(f"Seeded {allergy_count} allergy rules, {contra_count} contraindications, {ddi_count} DDIs.")

    conn.commit()
    conn.close()

    print("\n--- INGESTION SUMMARY STATISTICS ---")
    for k, v in stats.items():
        print(f"  {k}: {v:,}" if isinstance(v, int) else f"  {k}: {v}")
    print("=" * 70)

    return stats


if __name__ == "__main__":
    ingest_indian_pharmaceutical_catalog()
