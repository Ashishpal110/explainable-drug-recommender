"""
Unit tests for the Deterministic Safety Screening Engine (Phase 2B).
"""

import pytest
from app.safety.screening import SafetyScreeningEngine


@pytest.fixture
def engine():
    return SafetyScreeningEngine()


def test_no_matching_rule(engine):
    # Candidate with no recorded allergies or interacting meds
    res = engine.screen_candidate(
        candidate="Amlodipine",
        age=45,
        condition="Hypertension",
        allergies=[],
        current_medications=[],
    )
    assert res["safety_status"] == "NO_KNOWN_CONFLICT"
    assert res["severity"] == "NONE"
    assert len(res["allergy_conflicts"]) == 0
    assert len(res["ddi_warnings"]) == 0
    assert len(res["contraindications"]) == 0
    assert "No matching safety conflict" in res["explanation"]


def test_allergy_conflict(engine):
    # Lisinopril belongs to ACE Inhibitors
    res = engine.screen_candidate(
        candidate="Lisinopril",
        age=50,
        condition="Hypertension",
        allergies=["ACE Inhibitors"],
        current_medications=[],
    )
    assert res["safety_status"] == "FILTERED_SAFETY_CONFLICT"
    assert res["severity"] in ["CRITICAL", "HIGH"]
    assert len(res["allergy_conflicts"]) == 1
    assert res["allergy_conflicts"][0]["allergen_class"] == "ACE Inhibitors"
    assert "FDA SPL" in res["allergy_conflicts"][0]["source"]


def test_moderate_ddi(engine):
    # Lisinopril + Ibuprofen is MODERATE DDI
    res = engine.screen_candidate(
        candidate="Lisinopril",
        age=50,
        condition="Hypertension",
        allergies=[],
        current_medications=["Ibuprofen"],
    )
    assert res["safety_status"] == "WARNING"
    assert res["severity"] == "MODERATE"
    assert len(res["ddi_warnings"]) == 1
    assert res["ddi_warnings"][0]["interacting_drug_name"] == "Ibuprofen"
    assert "Recommended with caution" in res["explanation"]


def test_severe_ddi(engine):
    # Warfarin + Aspirin is HIGH severity bleeding risk
    res = engine.screen_candidate(
        candidate="Warfarin",
        age=60,
        condition="Atrial Fibrillation",
        allergies=[],
        current_medications=["Aspirin"],
    )
    assert res["safety_status"] == "FILTERED_SAFETY_CONFLICT"
    assert res["severity"] == "HIGH"
    assert len(res["ddi_warnings"]) == 1
    assert res["ddi_warnings"][0]["interacting_drug_name"] == "Aspirin"
    assert "FDA SPL" in res["ddi_warnings"][0]["source"]


def test_absolute_contraindication_age(engine):
    # Aspirin is contraindicated for age < 18 (Reye syndrome)
    res = engine.screen_candidate(
        candidate="Aspirin",
        age=10,
        condition="Fever",
        allergies=[],
        current_medications=[],
    )
    assert res["safety_status"] == "FILTERED_SAFETY_CONFLICT"
    assert res["severity"] == "ABSOLUTE"
    assert len(res["contraindications"]) == 1
    assert res["contraindications"][0]["trigger_value"] == "<18"
    assert "Reye syndrome" in res["contraindications"][0]["reason"]


def test_absolute_contraindication_condition(engine):
    # Ibuprofen in Peptic Ulcer Disease
    res = engine.screen_candidate(
        candidate="Ibuprofen",
        age=40,
        condition="Peptic Ulcer Disease",
        allergies=[],
        current_medications=[],
    )
    assert res["safety_status"] == "FILTERED_SAFETY_CONFLICT"
    assert res["severity"] == "ABSOLUTE"
    assert len(res["contraindications"]) == 1
    assert res["contraindications"][0]["trigger_value"] == "Peptic Ulcer Disease"


def test_multiple_simultaneous_conflicts(engine):
    # Lisinopril with ACE allergy AND Potassium chloride DDI AND Pregnancy
    res = engine.screen_candidate(
        candidate="Lisinopril",
        age=28,
        condition="Pregnancy",
        allergies=["ACE Inhibitors"],
        current_medications=["Potassium chloride"],
    )
    assert res["safety_status"] == "FILTERED_SAFETY_CONFLICT"
    assert len(res["allergy_conflicts"]) == 1
    assert len(res["ddi_warnings"]) == 1
    assert len(res["contraindications"]) == 1
    assert "ALLERGY_CONFLICT" in res["exact_rule_triggered"]
    assert "DRUG_INTERACTION" in res["exact_rule_triggered"]
    assert "CONTRAINDICATION" in res["exact_rule_triggered"]


def test_no_current_medications(engine):
    res = engine.screen_candidate(
        candidate="Metoprolol",
        age=45,
        condition="Hypertension",
        allergies=[],
        current_medications=[],
    )
    assert len(res["ddi_warnings"]) == 0
    assert res["safety_status"] == "NO_KNOWN_CONFLICT"


def test_unknown_current_medication(engine):
    # An unknown medication name should be handled gracefully without crashing
    res = engine.screen_candidate(
        candidate="Metoprolol",
        age=45,
        condition="Hypertension",
        allergies=[],
        current_medications=["NonExistentDrugXYZ999"],
    )
    assert len(res["ddi_warnings"]) == 0
    assert res["safety_status"] == "NO_KNOWN_CONFLICT"


def test_unknown_allergy_class(engine):
    # Unknown allergy class should not trigger false positive
    res = engine.screen_candidate(
        candidate="Metoprolol",
        age=45,
        condition="Hypertension",
        allergies=["PollenAllergy999"],
        current_medications=[],
    )
    assert len(res["allergy_conflicts"]) == 0
    assert res["safety_status"] == "NO_KNOWN_CONFLICT"


def test_no_fabricated_rule_for_unrelated_drugs(engine):
    # Acetaminophen + Metformin has no rule in our DB -> NO_KNOWN_CONFLICT
    res = engine.screen_candidate(
        candidate="Acetaminophen",
        age=50,
        condition="Headache",
        allergies=[],
        current_medications=["Metformin"],
    )
    assert res["safety_status"] == "NO_KNOWN_CONFLICT"
    assert len(res["ddi_warnings"]) == 0
