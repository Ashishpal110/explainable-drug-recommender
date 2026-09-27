"""
Deterministic Safety Screening Engine for allergy conflicts, DDIs, and contraindications.
"""

import sqlite3
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from app.core.config import settings


class SafetyScreeningEngine:
    """
    Deterministic clinical safety screening engine.
    Audits candidate drugs against patient allergies, active medications, and contraindications
    using explicitly stored rules in SQLite. Completely decoupled from recommendation ML scoring.
    """

    def __init__(self, db_path: Optional[Union[Path, str]] = None):
        self.db_path = Path(db_path) if db_path else settings.DATABASE_PATH

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def resolve_drug_id(self, drug_identifier: Union[int, str], cursor: sqlite3.Cursor) -> Optional[tuple[int, str]]:
        """
        Resolves a drug ID, brand name, generic name, or active ingredient to (drug_id, drug_name).
        """
        if isinstance(drug_identifier, int):
            cursor.execute("SELECT drug_id, name FROM drugs WHERE drug_id = ?;", (drug_identifier,))
            row = cursor.fetchone()
            if row:
                return row["drug_id"], row["name"]
        elif isinstance(drug_identifier, str):
            clean_str = drug_identifier.strip()
            # 1. Exact name match
            cursor.execute("SELECT drug_id, name FROM drugs WHERE LOWER(name) = LOWER(?);", (clean_str,))
            row = cursor.fetchone()
            if row:
                return row["drug_id"], row["name"]

            # 2. Exact generic name match
            cursor.execute("SELECT drug_id, name FROM drugs WHERE LOWER(generic_name) = LOWER(?);", (clean_str,))
            row = cursor.fetchone()
            if row:
                return row["drug_id"], row["name"]

            # 3. Canonical active ingredient match via drug_ingredients
            cursor.execute(
                """
                SELECT d.drug_id, d.name 
                FROM drugs d 
                JOIN drug_ingredients di ON d.drug_id = di.drug_id 
                WHERE LOWER(di.canonical_name) = LOWER(?) 
                LIMIT 1;
                """,
                (clean_str,)
            )
            row = cursor.fetchone()
            if row:
                return row["drug_id"], row["name"]

            # 4. Prefix / like search match
            cursor.execute("SELECT drug_id, name FROM drugs WHERE LOWER(name) LIKE ? LIMIT 1;", (clean_str.lower() + "%",))
            row = cursor.fetchone()
            if row:
                return row["drug_id"], row["name"]

        return None

    def evaluate_age_trigger(self, trigger_value: str, patient_age: Optional[int]) -> bool:
        """
        Evaluates age expressions such as '<18', '<12', '>65'.
        """
        if patient_age is None:
            return False

        match = re.match(r"^([<>]=?)\s*(\d+)$", trigger_value.strip())
        if not match:
            return False

        op, val_str = match.groups()
        target_val = int(val_str)

        if op == "<":
            return patient_age < target_val
        elif op == "<=":
            return patient_age <= target_val
        elif op == ">":
            return patient_age > target_val
        elif op == ">=":
            return patient_age >= target_val
        return False

    def screen_candidate(
        self,
        candidate: Union[int, str],
        age: Optional[int] = None,
        condition: Optional[str] = None,
        allergies: Optional[List[str]] = None,
        current_medications: Optional[List[Union[int, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Performs deterministic safety audit on a candidate drug.

        Returns structured dictionary containing:
        - candidate_drug_id
        - candidate_drug_name
        - safety_status ('NO_KNOWN_CONFLICT' | 'WARNING' | 'FILTERED_SAFETY_CONFLICT')
        - allergy_conflicts (list)
        - ddi_warnings (list)
        - contraindications (list)
        - exact_rule_triggered (str or None)
        - affected_items (list)
        - severity (str: 'CRITICAL', 'HIGH', 'MODERATE', 'LOW', or 'NONE')
        - clinical_reason (str or None)
        - explanation (str)
        """
        allergies = [a.strip() for a in (allergies or []) if a and a.strip()]
        current_medications = [m for m in (current_medications or []) if m]

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 1. Resolve Candidate
            resolved_candidate = self.resolve_drug_id(candidate, cursor)
            if not resolved_candidate:
                return {
                    "candidate_drug_id": candidate if isinstance(candidate, int) else None,
                    "candidate_drug_name": str(candidate),
                    "safety_status": "NO_KNOWN_CONFLICT",
                    "allergy_conflicts": [],
                    "ddi_warnings": [],
                    "contraindications": [],
                    "exact_rule_triggered": None,
                    "affected_items": [],
                    "severity": "NONE",
                    "clinical_reason": None,
                    "explanation": f"Candidate drug '{candidate}' is not present in the local database. No matching safety rules were triggered.",
                }

            drug_id, drug_name = resolved_candidate

            allergy_conflicts = []
            ddi_warnings = []
            contraindications = []
            affected_items = []
            max_severity = "NONE"

            severity_rank = {
                "NONE": 0,
                "LOW": 1,
                "RELATIVE": 1,
                "MODERATE": 2,
                "HIGH": 3,
                "ABSOLUTE": 4,
                "CRITICAL": 4,
            }

            # 2. Check Allergies
            if allergies:
                cursor.execute(
                    """
                    SELECT allergen_class, reaction_severity, notes, source
                    FROM allergy_crosswalk
                    WHERE drug_id = ?;
                    """,
                    (drug_id,),
                )
                rows = cursor.fetchall()
                patient_allergies_lower = {a.lower() for a in allergies}

                for row in rows:
                    if row["allergen_class"].lower() in patient_allergies_lower:
                        sev = row["reaction_severity"].upper()
                        allergy_conflicts.append({
                            "allergen_class": row["allergen_class"],
                            "severity": sev,
                            "notes": row["notes"],
                            "source": row["source"],
                        })
                        affected_items.append(f"Allergy: {row['allergen_class']}")
                        if severity_rank.get(sev, 0) > severity_rank.get(max_severity, 0):
                            max_severity = sev

            # 3. Check Drug-Drug Interactions
            if current_medications:
                # Resolve active medications to IDs
                med_ids_map = {}
                for med in current_medications:
                    res = self.resolve_drug_id(med, cursor)
                    if res:
                        med_ids_map[res[0]] = res[1]

                for med_id, med_name in med_ids_map.items():
                    if med_id == drug_id:
                        continue  # Skip identical drug

                    low_id, high_id = (drug_id, med_id) if drug_id < med_id else (med_id, drug_id)
                    cursor.execute(
                        """
                        SELECT severity, interaction_mechanism, clinical_action, source
                        FROM drug_interactions
                        WHERE drug_a_id = ? AND drug_b_id = ?;
                        """,
                        (low_id, high_id),
                    )
                    row = cursor.fetchone()
                    if row:
                        sev = row["severity"].upper()
                        ddi_warnings.append({
                            "interacting_drug_id": med_id,
                            "interacting_drug_name": med_name,
                            "severity": sev,
                            "interaction_mechanism": row["interaction_mechanism"],
                            "clinical_action": row["clinical_action"],
                            "source": row["source"],
                        })
                        affected_items.append(f"Interacting Medication: {med_name}")
                        if severity_rank.get(sev, 0) > severity_rank.get(max_severity, 0):
                            max_severity = sev

            # 4. Check Contraindications
            cursor.execute(
                """
                SELECT contraindication_type, trigger_value, severity, reason, source
                FROM contraindications
                WHERE drug_id = ?;
                """,
                (drug_id,),
            )
            for row in cursor.fetchall():
                c_type = row["contraindication_type"].upper()
                trigger = row["trigger_value"]
                sev = row["severity"].upper()
                is_triggered = False

                if c_type == "AGE" and age is not None:
                    is_triggered = self.evaluate_age_trigger(trigger, age)
                elif c_type == "CONDITION" and condition:
                    is_triggered = trigger.lower() in condition.lower() or condition.lower() in trigger.lower()
                elif c_type == "PREGNANCY" and condition:
                    is_triggered = "pregnancy" in condition.lower() or "pregnant" in condition.lower()

                if is_triggered:
                    contraindications.append({
                        "contraindication_type": c_type,
                        "trigger_value": trigger,
                        "severity": sev,
                        "reason": row["reason"],
                        "source": row["source"],
                    })
                    affected_items.append(f"Contraindication ({c_type}): {trigger}")
                    if severity_rank.get(sev, 0) > severity_rank.get(max_severity, 0):
                        max_severity = sev

            # 5. Determine Overall Safety Status
            # Precedence: FILTERED_SAFETY_CONFLICT > WARNING > NO_KNOWN_CONFLICT
            if severity_rank.get(max_severity, 0) >= severity_rank["HIGH"]:
                safety_status = "FILTERED_SAFETY_CONFLICT"
            elif severity_rank.get(max_severity, 0) >= severity_rank["MODERATE"]:
                safety_status = "WARNING"
            else:
                safety_status = "NO_KNOWN_CONFLICT"

            # 6. Build Exact Rule Description and Explanation
            exact_rule_triggered = None
            clinical_reasons = []

            rule_tags = []
            if allergy_conflicts:
                rule_tags.append("ALLERGY_CONFLICT")
                for ac in allergy_conflicts:
                    clinical_reasons.append(f"Patient exhibits recorded allergy to {ac['allergen_class']} (Source: {ac['source']}).")

            if ddi_warnings:
                rule_tags.append("DRUG_INTERACTION")
                for ddi in ddi_warnings:
                    clinical_reasons.append(
                        f"Co-administration with {ddi['interacting_drug_name']} ({ddi['severity']}): {ddi['interaction_mechanism']} "
                        f"Action: {ddi['clinical_action']} (Source: {ddi['source']})."
                    )

            if contraindications:
                rule_tags.append("CONTRAINDICATION")
                for c in contraindications:
                    clinical_reasons.append(f"Contraindicated ({c['severity']}) for {c['contraindication_type']} '{c['trigger_value']}': {c['reason']} (Source: {c['source']}).")

            if rule_tags:
                exact_rule_triggered = "_AND_".join(rule_tags)
                clinical_reason = " ".join(clinical_reasons)
                if safety_status == "FILTERED_SAFETY_CONFLICT":
                    explanation = f"Filtered due to critical safety constraints: {drug_name} matched {exact_rule_triggered.replace('_', ' ').lower()}. {clinical_reason}"
                else:
                    explanation = f"Recommended with caution: {drug_name} has moderate safety precautions. {clinical_reason}"
            else:
                clinical_reason = None
                explanation = f"No matching safety conflict was found for {drug_name} in the local safety knowledge base. (Note: Absence of a rule does NOT establish clinical safety)."

            return {
                "candidate_drug_id": drug_id,
                "candidate_drug_name": drug_name,
                "safety_status": safety_status,
                "allergy_conflicts": allergy_conflicts,
                "ddi_warnings": ddi_warnings,
                "contraindications": contraindications,
                "exact_rule_triggered": exact_rule_triggered,
                "affected_items": affected_items,
                "severity": max_severity,
                "clinical_reason": clinical_reason,
                "explanation": explanation,
            }

        finally:
            conn.close()
