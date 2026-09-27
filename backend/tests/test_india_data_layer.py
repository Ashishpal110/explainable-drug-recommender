"""
Comprehensive test suite for the Indian Pharmaceutical Data Layer, Brand Normalization,
Composition Parsing, Multi-salt FDCs, Condition Provenance, and Ingredient-Level Safety Screening.
"""

import sqlite3
import pytest
from pathlib import Path
from app.core.config import settings
from app.data.normalization import (
    extract_brand_and_dosage_form,
    get_canonical_ingredient_name,
    parse_single_composition,
    parse_drug_compositions,
    normalize_manufacturer_name,
)
from app.safety.screening import SafetyScreeningEngine
from app.ml.sentiment import SentimentModel


@pytest.fixture(scope="module")
def db_conn():
    conn = sqlite3.connect(str(settings.DATABASE_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def safety_engine():
    return SafetyScreeningEngine()


@pytest.fixture(scope="module")
def sentiment_model():
    return SentimentModel()


def test_brand_name_and_dosage_form_extraction():
    """
    Test 1: Brand normalization and dosage form extraction on Indian trade names.
    """
    # Dolo 650
    brand, form = extract_brand_and_dosage_form("Dolo 650 Tablet")
    assert brand == "Dolo 650"
    assert form == "Tablet"

    # Augmentin 625 Duo
    brand, form = extract_brand_and_dosage_form("Augmentin 625 Duo Tablet")
    assert "Augmentin 625 Duo" in brand
    assert form == "Tablet"

    # Ascoril LS Syrup
    brand, form = extract_brand_and_dosage_form("Ascoril LS Syrup")
    assert brand == "Ascoril LS"
    assert form == "Syrup"

    # Generic injection
    brand, form = extract_brand_and_dosage_form("Chophos 200mg Injection")
    assert "Chophos 200mg" in brand
    assert form == "Injection"


def test_composition_parsing_single_ingredient():
    """
    Test 2 & 3: Single active chemical salt and strength parsing.
    """
    parsed = parse_single_composition("Paracetamol (650mg)")
    assert parsed is not None
    assert parsed["active_ingredient"] == "Paracetamol"
    assert parsed["strength_value"] == 650.0
    assert parsed["strength_unit"] == "mg"
    assert parsed["canonical_name"] == "paracetamol"
    assert parsed["parsing_status"] == "SUCCESS"

    parsed_az = parse_single_composition("Azithromycin (500mg)")
    assert parsed_az is not None
    assert parsed_az["active_ingredient"] == "Azithromycin"
    assert parsed_az["strength_value"] == 500.0
    assert parsed_az["strength_unit"] == "mg"
    assert parsed_az["canonical_name"] == "azithromycin"


def test_combination_drug_multi_ingredient_parsing():
    """
    Test 4 & 5: Multi-salt Fixed Dose Combination (FDC) parsing.
    """
    # Augmentin: Amoxicillin + Clavulanic Acid
    ings = parse_drug_compositions("Amoxycillin (500mg)", "Clavulanic Acid (125mg)")
    assert len(ings) == 2
    assert ings[0]["canonical_name"] == "amoxicillin"
    assert ings[0]["strength_value"] == 500.0
    assert ings[1]["canonical_name"] == "clavulanic acid"
    assert ings[1]["strength_value"] == 125.0

    # Telmisartan + HCTZ combination
    ings_telma = parse_drug_compositions("Telmisartan (40mg)", "Hydrochlorothiazide (12.5mg)")
    assert len(ings_telma) == 2
    assert ings_telma[0]["canonical_name"] == "telmisartan"
    assert ings_telma[0]["strength_value"] == 40.0
    assert ings_telma[1]["canonical_name"] == "hydrochlorothiazide"
    assert ings_telma[1]["strength_value"] == 12.5


def test_canonical_ingredient_synonym_normalization():
    """
    Test 6: Pharmacopoeia synonym harmonization to canonical INN names.
    """
    assert get_canonical_ingredient_name("Amoxycillin") == "amoxicillin"
    assert get_canonical_ingredient_name("Acetaminophen") == "paracetamol"
    assert get_canonical_ingredient_name("Metformin Hydrochloride") == "metformin"
    assert get_canonical_ingredient_name("Amlodipine Besylate") == "amlodipine"
    assert get_canonical_ingredient_name("Levosalbutamol") == "levalbuterol"
    assert get_canonical_ingredient_name("Atorvastatin Calcium") == "atorvastatin"


def test_database_indian_catalog_presence(db_conn):
    """
    Test 7 & 10: Database contains ingested Indian catalog, active ingredients, and schema constraints.
    """
    cursor = db_conn.cursor()

    # Verify table counts
    cursor.execute("SELECT COUNT(*) FROM drugs;")
    drug_count = cursor.fetchone()[0]
    assert drug_count > 100000

    cursor.execute("SELECT COUNT(*) FROM drug_ingredients;")
    ingredient_count = cursor.fetchone()[0]
    assert ingredient_count > 100000

    cursor.execute("SELECT COUNT(*) FROM drug_conditions;")
    dc_count = cursor.fetchone()[0]
    assert dc_count > 100000

    # Check specific Indian benchmark drugs
    cursor.execute("SELECT drug_id, name, generic_name, manufacturer, price_inr, dosage_form FROM drugs WHERE name LIKE 'Dolo 650%';")
    dolo_row = cursor.fetchone()
    assert dolo_row is not None
    assert "Dolo 650" in dolo_row["name"]
    assert "paracetamol" in dolo_row["generic_name"].lower()
    assert dolo_row["price_inr"] > 0

    cursor.execute("SELECT drug_id, name, generic_name, manufacturer, price_inr FROM drugs WHERE name LIKE 'Augmentin 625 Duo%';")
    aug_row = cursor.fetchone()
    assert aug_row is not None
    assert "amoxicillin" in aug_row["generic_name"].lower()
    assert "clavulanic acid" in aug_row["generic_name"].lower()


def test_condition_mapping_and_evidence_provenance(db_conn):
    """
    Test 8: Condition mappings contain valid evidence sources (NFI / CDSCO).
    """
    cursor = db_conn.cursor()
    cursor.execute(
        """
        SELECT dc.drug_id, d.name, c.name AS condition_name, dc.evidence_source, dc.indication_type
        FROM drug_conditions dc
        JOIN drugs d ON dc.drug_id = d.drug_id
        JOIN conditions c ON dc.condition_id = c.condition_id
        WHERE d.name LIKE 'Dolo 650%'
        LIMIT 5;
        """
    )
    rows = cursor.fetchall()
    assert len(rows) > 0
    for r in rows:
        assert "National Formulary of India" in r["evidence_source"] or "CDSCO" in r["evidence_source"]
        assert r["condition_name"] in ["Fever", "Pain", "Headache", "Osteoarthritis"]


def test_safety_ingredient_level_allergy_screening(safety_engine):
    """
    Test 9: Safety screening on Indian brand names using active ingredient crosswalk.
    Augmentin 625 Duo (contains amoxicillin) screened against Penicillin allergy -> FILTERED.
    """
    res = safety_engine.screen_candidate(
        candidate="Augmentin 625 Duo Tablet",
        allergies=["Penicillins"],
    )
    assert res["safety_status"] == "FILTERED_SAFETY_CONFLICT"
    assert "ALLERGY_CONFLICT" in res["exact_rule_triggered"]
    assert res["severity"] in ("HIGH", "CRITICAL")
    assert any("Penicillins" in item for item in res["affected_items"])


def test_safety_ingredient_level_ddi_screening(safety_engine):
    """
    Test 9b: DDI screening between Indian brands (e.g. Warfarin vs Ecosprin / Aspirin).
    """
    res = safety_engine.screen_candidate(
        candidate="Aspirin",
        current_medications=["Warfarin"],
    )
    assert res["safety_status"] in ("WARNING", "FILTERED_SAFETY_CONFLICT")
    assert len(res["ddi_warnings"]) > 0
    assert "Warfarin" in str(res["ddi_warnings"])


def test_sentiment_lookup_preservation_and_active_ingredient_link(sentiment_model):
    """
    Test: Preserves existing sentiment model and maps active generic ingredient scores without fabricating sentiment.
    """
    # 1. Existing benchmark drug
    score_lisinopril = sentiment_model.get_drug_sentiment("Lisinopril")
    assert score_lisinopril is not None
    assert 0.0 <= score_lisinopril <= 1.0

    # 2. Indian brand with generic link
    score_dolo = sentiment_model.get_drug_sentiment("Dolo 650 Tablet", generic_name="paracetamol")
    assert score_dolo is not None
    assert 0.0 <= score_dolo <= 1.0

    # 3. Unreviewed unknown entity returns None without fabricating sentiment
    score_unknown = sentiment_model.get_drug_sentiment("NonExistentUnverifiedChemical999")
    assert score_unknown is None, "Unreviewed drugs must return None without assigning synthetic 0.50 score"

