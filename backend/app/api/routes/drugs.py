"""
Catalog routes for drugs, medical conditions, and allergen classes.
"""

import sqlite3
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.core.config import settings

router = APIRouter(tags=["Drugs & Conditions Catalog"])


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.DATABASE_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


# --- Schema Definitions ---

class ConditionItem(BaseModel):
    condition_id: int
    name: str
    category: str
    drug_count: int


class ConditionsListResponse(BaseModel):
    total_conditions: int
    conditions: List[ConditionItem]


class AllergiesListResponse(BaseModel):
    allergen_classes: List[str]


class DrugListItem(BaseModel):
    drug_id: int
    name: str
    generic_name: Optional[str] = None
    drug_class: str
    avg_rating: float
    total_reviews: int
    positive_sentiment_ratio: float


class DrugListResponse(BaseModel):
    total_drugs: int
    limit: int
    offset: int
    drugs: List[DrugListItem]


class DrugDetailResponse(BaseModel):
    drug_id: int
    name: str
    generic_name: Optional[str] = None
    drug_class: str
    description: str
    avg_rating: float
    total_reviews: int
    positive_sentiment_ratio: float
    indicated_conditions: List[Dict[str, Any]]
    allergy_classes: List[str]
    contraindications: List[Dict[str, Any]]
    interaction_count: int


# --- Endpoints ---

@router.get("/conditions", response_model=ConditionsListResponse)
async def list_conditions() -> ConditionsListResponse:
    """
    Returns indexed medical conditions with mapped drug counts.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                c.condition_id,
                c.name,
                c.category,
                COUNT(dc.drug_id) AS drug_count
            FROM conditions c
            LEFT JOIN drug_conditions dc ON c.condition_id = dc.condition_id
            GROUP BY c.condition_id, c.name, c.category
            ORDER BY drug_count DESC, c.name ASC;
            """
        )
        rows = cursor.fetchall()
        conditions = [
            ConditionItem(
                condition_id=r["condition_id"],
                name=r["name"],
                category=r["category"] or "General",
                drug_count=int(r["drug_count"]),
            )
            for r in rows
        ]
        return ConditionsListResponse(
            total_conditions=len(conditions),
            conditions=conditions,
        )
    finally:
        conn.close()


@router.get("/allergies", response_model=AllergiesListResponse)
async def list_allergies() -> AllergiesListResponse:
    """
    Returns distinct allergen and pharmacological classes supported by the safety crosswalk.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT allergen_class FROM allergy_crosswalk ORDER BY allergen_class ASC;")
        rows = cursor.fetchall()
        classes = [r["allergen_class"] for r in rows if r["allergen_class"]]
        return AllergiesListResponse(allergen_classes=classes)
    finally:
        conn.close()


@router.get("/drugs", response_model=DrugListResponse)
async def list_drugs(
    condition: Optional[str] = Query(None, description="Filter by condition name or substring"),
    search: Optional[str] = Query(None, description="Search by drug name or generic name"),
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> DrugListResponse:
    """
    Paginated search and listing of cataloged medications from SQLite.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        where_clauses = []
        params: List[Any] = []

        if condition and condition.strip():
            where_clauses.append(
                """
                d.drug_id IN (
                    SELECT dc.drug_id FROM drug_conditions dc
                    JOIN conditions c ON dc.condition_id = c.condition_id
                    WHERE LOWER(c.name) LIKE LOWER(?)
                )
                """
            )
            params.append(f"%{condition.strip()}%")

        if search and search.strip():
            where_clauses.append("(LOWER(d.name) LIKE LOWER(?) OR LOWER(d.generic_name) LIKE LOWER(?))")
            params.extend([f"%{search.strip()}%", f"%{search.strip()}%"])

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Total count query
        count_sql = f"SELECT COUNT(*) AS total FROM drugs d {where_sql};"
        cursor.execute(count_sql, params)
        total_drugs = cursor.fetchone()["total"]

        # Data query
        query_sql = f"""
            SELECT 
                d.drug_id,
                d.name,
                d.generic_name,
                d.drug_class,
                d.avg_rating,
                d.total_reviews,
                d.positive_sentiment_ratio
            FROM drugs d
            {where_sql}
            ORDER BY d.total_reviews DESC, d.name ASC
            LIMIT ? OFFSET ?;
        """
        data_params = params + [limit, offset]
        cursor.execute(query_sql, data_params)
        rows = cursor.fetchall()

        drugs = [
            DrugListItem(
                drug_id=r["drug_id"],
                name=r["name"],
                generic_name=r["generic_name"],
                drug_class=r["drug_class"] or "Not specified",
                avg_rating=round(float(r["avg_rating"] or 0.0), 2),
                total_reviews=int(r["total_reviews"] or 0),
                positive_sentiment_ratio=round(float(r["positive_sentiment_ratio"] or 0.0), 4),
            )
            for r in rows
        ]

        return DrugListResponse(
            total_drugs=total_drugs,
            limit=limit,
            offset=offset,
            drugs=drugs,
        )
    finally:
        conn.close()


@router.get("/drugs/{drug_id}", response_model=DrugDetailResponse)
async def get_drug_detail(drug_id: int) -> DrugDetailResponse:
    """
    Returns detailed profile, review statistics, indicated conditions, and safety rules for a medication.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # 1. Drug Profile
        cursor.execute(
            """
            SELECT drug_id, name, generic_name, drug_class, description, avg_rating, total_reviews, positive_sentiment_ratio
            FROM drugs
            WHERE drug_id = ?;
            """,
            (drug_id,),
        )
        drug_row = cursor.fetchone()
        if not drug_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Drug with ID {drug_id} was not found in catalog.",
            )

        # 2. Indicated Conditions
        cursor.execute(
            """
            SELECT c.condition_id, c.name AS condition_name, dc.review_count, dc.avg_rating
            FROM drug_conditions dc
            JOIN conditions c ON dc.condition_id = c.condition_id
            WHERE dc.drug_id = ?
            ORDER BY dc.review_count DESC;
            """,
            (drug_id,),
        )
        conditions_rows = cursor.fetchall()
        indicated_conditions = [
            {
                "condition_id": r["condition_id"],
                "condition_name": r["condition_name"],
                "review_count": int(r["review_count"]),
                "avg_rating": round(float(r["avg_rating"] or 0.0), 2),
            }
            for r in conditions_rows
        ]

        # 3. Allergy Classes
        cursor.execute(
            """
            SELECT allergen_class, reaction_severity, notes, source
            FROM allergy_crosswalk
            WHERE drug_id = ?;
            """,
            (drug_id,),
        )
        allergy_rows = cursor.fetchall()
        allergy_classes = [r["allergen_class"] for r in allergy_rows]

        # 4. Contraindications
        cursor.execute(
            """
            SELECT contraindication_type, trigger_value, severity, reason, source
            FROM contraindications
            WHERE drug_id = ?;
            """,
            (drug_id,),
        )
        contra_rows = cursor.fetchall()
        contraindications = [
            {
                "type": r["contraindication_type"],
                "trigger": r["trigger_value"],
                "severity": r["severity"],
                "reason": r["reason"],
                "source": r["source"],
            }
            for r in contra_rows
        ]

        # 5. Interaction Count
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM drug_interactions
            WHERE drug_a_id = ? OR drug_b_id = ?;
            """,
            (drug_id, drug_id),
        )
        interaction_count = int(cursor.fetchone()["cnt"])

        return DrugDetailResponse(
            drug_id=drug_row["drug_id"],
            name=drug_row["name"],
            generic_name=drug_row["generic_name"],
            drug_class=drug_row["drug_class"] or "Not specified",
            description=drug_row["description"] or f"Medication entry for {drug_row['name']}.",
            avg_rating=round(float(drug_row["avg_rating"] or 0.0), 2),
            total_reviews=int(drug_row["total_reviews"] or 0),
            positive_sentiment_ratio=round(float(drug_row["positive_sentiment_ratio"] or 0.0), 4),
            indicated_conditions=indicated_conditions,
            allergy_classes=allergy_classes,
            contraindications=contraindications,
            interaction_count=interaction_count,
        )
    finally:
        conn.close()
