"""
Idempotent script to seed verified safety rules into SQLite Layer 2 tables.
"""

import json
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "drug_system.db"
SAFETY_JSON_PATH = PROJECT_ROOT / "data" / "safety" / "verified_safety_rules.json"


def seed_safety_rules():
    print("=" * 60)
    print("PHASE 2B: SEEDING VERIFIED SAFETY RULES")
    print("=" * 60)

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Run preprocessing first.")

    if not SAFETY_JSON_PATH.exists():
        raise FileNotFoundError(f"Safety JSON not found at {SAFETY_JSON_PATH}")

    with open(SAFETY_JSON_PATH, "r", encoding="utf-8") as f:
        safety_data = json.load(f)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # Build drugName -> drug_id mapping
    cursor.execute("SELECT LOWER(name), drug_id, name FROM drugs;")
    drug_map = {}
    for lower_name, drug_id, orig_name in cursor.fetchall():
        drug_map[lower_name] = drug_id

    # Begin transaction
    cursor.execute("BEGIN TRANSACTION;")

    # 1. Clear existing safety tables for idempotency
    cursor.execute("DELETE FROM allergy_crosswalk;")
    cursor.execute("DELETE FROM drug_interactions;")
    cursor.execute("DELETE FROM contraindications;")

    # 2. Seed Allergy Crosswalk
    allergy_count = 0
    for item in safety_data.get("allergies", []):
        drug_name_clean = item["drug_name"].strip().lower()
        if drug_name_clean not in drug_map:
            print(f"WARNING: Drug '{item['drug_name']}' not found in database. Skipping.")
            continue
        drug_id = drug_map[drug_name_clean]
        cursor.execute(
            """
            INSERT INTO allergy_crosswalk (drug_id, allergen_class, reaction_severity, notes, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                drug_id,
                item["allergen_class"].strip(),
                item.get("reaction_severity", "HIGH"),
                item.get("notes"),
                item["source"],
            ),
        )
        allergy_count += 1

    # 3. Seed Drug-Drug Interactions (unordered pair: drug_a_id < drug_b_id)
    ddi_count = 0
    seen_pairs = set()
    for item in safety_data.get("interactions", []):
        name_a = item["drug_a"].strip().lower()
        name_b = item["drug_b"].strip().lower()

        if name_a not in drug_map or name_b not in drug_map:
            print(f"WARNING: Interaction pair ({item['drug_a']}, {item['drug_b']}) not fully resolved. Skipping.")
            continue

        id_a = drug_map[name_a]
        id_b = drug_map[name_b]

        # Enforce drug_a_id < drug_b_id
        if id_a == id_b:
            print(f"WARNING: Self-interaction on {item['drug_a']} skipped.")
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
                item["severity"].strip().upper(),
                item["interaction_mechanism"].strip(),
                item["clinical_action"].strip(),
                item["source"].strip(),
            ),
        )
        ddi_count += 1

    # 4. Seed Contraindications
    contra_count = 0
    for item in safety_data.get("contraindications", []):
        drug_name_clean = item["drug_name"].strip().lower()
        if drug_name_clean not in drug_map:
            print(f"WARNING: Drug '{item['drug_name']}' not found in database. Skipping.")
            continue
        drug_id = drug_map[drug_name_clean]
        cursor.execute(
            """
            INSERT INTO contraindications (drug_id, contraindication_type, trigger_value, severity, reason, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                drug_id,
                item["contraindication_type"].strip().upper(),
                item["trigger_value"].strip(),
                item.get("severity", "ABSOLUTE").strip().upper(),
                item["reason"].strip(),
                item["source"].strip(),
            ),
        )
        contra_count += 1

    conn.commit()

    # Verification queries
    cursor.execute("SELECT COUNT(*) FROM allergy_crosswalk;")
    actual_allergies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM drug_interactions;")
    actual_ddis = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM contraindications;")
    actual_contras = cursor.fetchone()[0]

    # Verify foreign keys
    cursor.execute(
        """
        SELECT COUNT(*) FROM allergy_crosswalk ac
        LEFT JOIN drugs d ON ac.drug_id = d.drug_id
        WHERE d.drug_id IS NULL;
        """
    )
    allergy_orphans = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM drug_interactions di
        LEFT JOIN drugs da ON di.drug_a_id = da.drug_id
        LEFT JOIN drugs db ON di.drug_b_id = db.drug_id
        WHERE da.drug_id IS NULL OR db.drug_id IS NULL;
        """
    )
    ddi_orphans = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM contraindications c
        LEFT JOIN drugs d ON c.drug_id = d.drug_id
        WHERE d.drug_id IS NULL;
        """
    )
    contra_orphans = cursor.fetchone()[0]

    conn.close()

    print(f"Seeded Allergy Rules:         {actual_allergies}")
    print(f"Seeded Interaction Pairs:     {actual_ddis}")
    print(f"Seeded Contraindication Rules:{actual_contras}")
    print(f"Orphan Foreign Keys:          Allergies: {allergy_orphans}, DDIs: {ddi_orphans}, Contra: {contra_orphans}")
    print("=" * 60)


if __name__ == "__main__":
    seed_safety_rules()
