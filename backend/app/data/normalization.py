"""
Deterministic normalization and parsing utilities for Indian pharmaceutical data.
Handles brand name normalization, dosage form extraction, chemical composition parsing,
strength extraction, and canonical active ingredient standardization.
"""

import re
from typing import Dict, List, Optional, Tuple, Any

# Standard dosage forms sorted by length descending for accurate greedy matching
DOSAGE_FORMS = [
    "Eye/Ear Drops", "Eye Drops", "Ear Drops", "Nasal Drops", "Nasal Spray",
    "Dusting Powder", "Effervescent Tablet", "Chewable Tablet", "Dispersible Tablet",
    "Mouth Dissolving Tablet", "Sustained Release Tablet", "Extended Release Tablet",
    "Tablet", "Tablets", "Capsule", "Capsules", "Syrup", "Injection", "Ointment",
    "Cream", "Gel", "Drops", "Drop", "Inhaler", "Suspension", "Solution", "Lotion",
    "Infusion", "Powder", "Mouthwash", "Spray", "Shampoo", "Patch", "Suppository",
    "Granules", "Sachet", "Emulsion", "Liniment", "Gargle", "Expectorant", "Soap",
    "Dry Syrup", "Respules", "Rotacaps", "Transcaps", "Gel Wash"
]

_DOSAGE_FORMS_SORTED = sorted(DOSAGE_FORMS, key=len, reverse=True)
_FORM_PATTERN = re.compile(r"\b(" + "|".join(re.escape(f) for f in _DOSAGE_FORMS_SORTED) + r")\b", re.IGNORECASE)

# Standard composition regex: matches 'Salt Name (Strength Unit)' or 'Salt Name (Strength)'
# Examples: 'Amoxycillin (500mg)', 'Clavulanic Acid (125mg)', 'Ambroxol (30mg/5ml)', 'Clobetasol (0.05% w/w)'
_COMP_PATTERN = re.compile(
    r"^(.*?)\s*\(\s*(\d+(?:\.\d+)?)\s*([a-zA-Z%/\s\d]+?)\s*\)$"
)

# Canonical ingredient synonym dictionary (Indian/British Pharmacopoeia to International Nonproprietary Name / INN)
CANONICAL_SYNONYMS: Dict[str, str] = {
    "amoxycillin": "amoxicillin",
    "paracetamol": "paracetamol",
    "acetaminophen": "paracetamol",
    "clavulanic acid": "clavulanic acid",
    "potassium clavulanate": "clavulanic acid",
    "levosalbutamol": "levalbuterol",
    "salbutamol": "albuterol",
    "metformin hydrochloride": "metformin",
    "metformin": "metformin",
    "glimepiride": "glimepiride",
    "telmisartan": "telmisartan",
    "amlodipine besylate": "amlodipine",
    "amlodipine": "amlodipine",
    "atorvastatin calcium": "atorvastatin",
    "atorvastatin": "atorvastatin",
    "rosuvastatin calcium": "rosuvastatin",
    "rosuvastatin": "rosuvastatin",
    "pantoprazole sodium": "pantoprazole",
    "pantoprazole": "pantoprazole",
    "rabeprazole sodium": "rabeprazole",
    "rabeprazole": "rabeprazole",
    "omeprazole": "omeprazole",
    "esomeprazole": "esomeprazole",
    "azithromycin": "azithromycin",
    "azithromycin dihydrate": "azithromycin",
    "cefixime": "cefixime",
    "cefpodoxime proxetil": "cefpodoxime",
    "cefpodoxime": "cefpodoxime",
    "ceftriaxone": "ceftriaxone",
    "cefuroxime axetil": "cefuroxime",
    "cefuroxime": "cefuroxime",
    "ciprofloxacin": "ciprofloxacin",
    "ciprofloxacin hydrochloride": "ciprofloxacin",
    "ofloxacin": "ofloxacin",
    "levofloxacin": "levofloxacin",
    "levocetirizine": "levocetirizine",
    "levocetirizine dihydrochloride": "levocetirizine",
    "cetirizine": "cetirizine",
    "cetirizine hydrochloride": "cetirizine",
    "montelukast": "montelukast",
    "montelukast sodium": "montelukast",
    "aceclofenac": "aceclofenac",
    "diclofenac sodium": "diclofenac",
    "diclofenac potassium": "diclofenac",
    "diclofenac": "diclofenac",
    "ibuprofen": "ibuprofen",
    "naproxen": "naproxen",
    "etoricoxib": "etoricoxib",
    "mefenamic acid": "mefenamic acid",
    "nimesulide": "nimesulide",
    "aspirin": "aspirin",
    "acetylsalicylic acid": "aspirin",
    "clopidogrel": "clopidogrel",
    "clopidogrel bisulfate": "clopidogrel",
    "hydrochlorothiazide": "hydrochlorothiazide",
    "losartan": "losartan",
    "losartan potassium": "losartan",
    "lisinopril": "lisinopril",
    "ramipril": "ramipril",
    "enalapril": "enalapril",
    "vildagliptin": "vildagliptin",
    "teneligliptin": "teneligliptin",
    "sitagliptin": "sitagliptin",
    "dapagliflozin": "dapagliflozin",
    "empagliflozin": "empagliflozin",
    "glipizide": "glipizide",
    "gliclazide": "gliclazide",
    "voglibose": "voglibose",
    "pioglitazone": "pioglitazone",
    "domperidone": "domperidone",
    "ondansetron": "ondansetron",
    "ondansetron hydrochloride": "ondansetron",
    "itraconazole": "itraconazole",
    "fluconazole": "fluconazole",
    "pregabalin": "pregabalin",
    "gabapentin": "gabapentin",
    "methylcobalamin": "methylcobalamin",
    "folic acid": "folic acid",
    "ambroxol": "ambroxol",
    "ambroxol hydrochloride": "ambroxol",
    "guaifenesin": "guaifenesin",
    "chlorpheniramine maleate": "chlorpheniramine",
    "phenylephrine hydrochloride": "phenylephrine",
    "phenylephrine": "phenylephrine",
    "dextromethorphan": "dextromethorphan",
    "dextromethorphan hydrobromide": "dextromethorphan",
    "tramadol": "tramadol",
    "tramadol hydrochloride": "tramadol",
    "warfarin": "warfarin",
    "warfarin sodium": "warfarin",
}


def extract_brand_and_dosage_form(raw_name: str) -> Tuple[str, str]:
    """
    Extracts the clean brand name and standardized dosage form from a raw medicine trade name.
    Example: 'Dolo 650 Tablet' -> ('Dolo 650', 'Tablet')
    """
    if not isinstance(raw_name, str) or not raw_name.strip():
        return ("", "Not specified")

    name_str = raw_name.strip()
    match = _FORM_PATTERN.search(name_str)
    if match:
        form = match.group(1).title()
        # Clean brand name by stripping dosage form match
        brand = _FORM_PATTERN.sub("", name_str).strip()
        brand = re.sub(r"\s+", " ", brand).strip(" -/,")
        return (brand if brand else name_str, form)

    return (name_str, "Not specified")


def get_canonical_ingredient_name(raw_salt: str) -> str:
    """
    Normalizes a salt name to its canonical INN (International Nonproprietary Name) lower-case format.
    Example: 'Amoxycillin' -> 'amoxicillin', 'Paracetamol' -> 'paracetamol'
    """
    if not isinstance(raw_salt, str) or not raw_salt.strip():
        return ""

    cleaned = raw_salt.strip().lower()
    # Remove trailing salt forms like 'hcl', 'hydrochloride', 'sodium', etc., if not matched directly
    if cleaned in CANONICAL_SYNONYMS:
        return CANONICAL_SYNONYMS[cleaned]

    # Attempt regex cleanup of common chemical suffixes
    base = re.sub(r"\b(hydrochloride|hcl|sodium|potassium|calcium|besylate|dihydrate|trihydrate|monohydrate|maleate|sulfate|tartrate|fumarate|phosphate|mesylate)\b", "", cleaned).strip()
    if base in CANONICAL_SYNONYMS:
        return CANONICAL_SYNONYMS[base]

    return base if base else cleaned


def parse_single_composition(comp_str: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Parses a single composition string into its constituent parts:
    - active_ingredient (raw string)
    - strength_value (float or None)
    - strength_unit (str or None)
    - canonical_name (standardized INN)
    - raw (original string)
    """
    if not isinstance(comp_str, str) or not comp_str.strip() or comp_str.strip().lower() in ("nan", "none", "null"):
        return None

    cleaned_str = comp_str.strip()
    match = _COMP_PATTERN.match(cleaned_str)

    if match:
        salt = match.group(1).strip()
        strength_val = float(match.group(2))
        strength_unit = match.group(3).strip()
        canonical = get_canonical_ingredient_name(salt)
        return {
            "active_ingredient": salt,
            "strength_value": strength_val,
            "strength_unit": strength_unit,
            "canonical_name": canonical,
            "raw": cleaned_str,
            "parsing_status": "SUCCESS"
        }
    else:
        # Fallback for strings without clean '(strength)' format
        canonical = get_canonical_ingredient_name(cleaned_str)
        return {
            "active_ingredient": cleaned_str,
            "strength_value": None,
            "strength_unit": None,
            "canonical_name": canonical,
            "raw": cleaned_str,
            "parsing_status": "PARTIAL_NO_STRENGTH"
        }


def parse_drug_compositions(short_comp1: Optional[str], short_comp2: Optional[str]) -> List[Dict[str, Any]]:
    """
    Parses primary and secondary composition fields of a medicine into a structured list
    of constituent active ingredients.
    """
    ingredients = []

    p1 = parse_single_composition(short_comp1)
    if p1:
        ingredients.append(p1)

    p2 = parse_single_composition(short_comp2)
    if p2:
        ingredients.append(p2)

    return ingredients


def normalize_manufacturer_name(mfr: Optional[str]) -> str:
    """
    Cleans corporate name variations for Indian manufacturers.
    """
    if not isinstance(mfr, str) or not mfr.strip():
        return "Unknown Manufacturer"
    cleaned = re.sub(r"\s+", " ", mfr.strip())
    return cleaned
