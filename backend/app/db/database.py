"""
Database connection, initialization, and session management for SQLite.
"""

import sqlite3
from pathlib import Path
from typing import Generator
from app.core.config import settings

SCHEMA_SQL = """
-- Layer 1: ML & Review-Derived Knowledge Store
CREATE TABLE IF NOT EXISTS drugs (
    drug_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    generic_name TEXT,
    composition TEXT,
    drug_class TEXT NOT NULL DEFAULT 'Not specified',
    manufacturer TEXT,
    price_inr REAL DEFAULT 0.0,
    dosage_form TEXT DEFAULT 'Not specified',
    pack_size TEXT,
    is_discontinued INTEGER DEFAULT 0,
    description TEXT,
    avg_rating REAL DEFAULT 0.0,
    total_reviews INTEGER DEFAULT 0,
    positive_sentiment_ratio REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_drugs_name ON drugs(name);
CREATE INDEX IF NOT EXISTS idx_drugs_generic_name ON drugs(generic_name);
CREATE INDEX IF NOT EXISTS idx_drugs_drug_class ON drugs(drug_class);
CREATE INDEX IF NOT EXISTS idx_drugs_manufacturer ON drugs(manufacturer);

-- Structured Active Ingredients per Drug (Supports Multi-salt FDCs)
CREATE TABLE IF NOT EXISTS drug_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id INTEGER NOT NULL,
    active_ingredient TEXT NOT NULL,
    strength_value REAL,
    strength_unit TEXT,
    canonical_name TEXT NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (drug_id) REFERENCES drugs(drug_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_di_drug_id ON drug_ingredients(drug_id);
CREATE INDEX IF NOT EXISTS idx_di_canonical_name ON drug_ingredients(canonical_name);

CREATE TABLE IF NOT EXISTS conditions (
    condition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT DEFAULT 'General'
);

CREATE INDEX IF NOT EXISTS idx_conditions_name ON conditions(name);

CREATE TABLE IF NOT EXISTS drug_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id INTEGER NOT NULL,
    condition_id INTEGER NOT NULL,
    review_count INTEGER DEFAULT 0,
    avg_rating REAL DEFAULT 0.0,
    indication_type TEXT DEFAULT 'Primary',
    evidence_source TEXT DEFAULT 'Clinical Literature',
    FOREIGN KEY (drug_id) REFERENCES drugs(drug_id) ON DELETE CASCADE,
    FOREIGN KEY (condition_id) REFERENCES conditions(condition_id) ON DELETE CASCADE,
    UNIQUE(drug_id, condition_id)
);

CREATE INDEX IF NOT EXISTS idx_dc_drug_id ON drug_conditions(drug_id);
CREATE INDEX IF NOT EXISTS idx_dc_condition_id ON drug_conditions(condition_id);

-- Layer 2: Deterministic Safety Knowledge Base (Tables created, populated in Phase 2B)
CREATE TABLE IF NOT EXISTS allergy_crosswalk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id INTEGER NOT NULL,
    allergen_class TEXT NOT NULL,
    reaction_severity TEXT DEFAULT 'HIGH',
    notes TEXT,
    source TEXT NOT NULL,
    FOREIGN KEY (drug_id) REFERENCES drugs(drug_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_allergy_drug_id ON allergy_crosswalk(drug_id);
CREATE INDEX IF NOT EXISTS idx_allergy_class ON allergy_crosswalk(allergen_class);

CREATE TABLE IF NOT EXISTS drug_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_a_id INTEGER NOT NULL,
    drug_b_id INTEGER NOT NULL,
    severity TEXT NOT NULL,
    interaction_mechanism TEXT NOT NULL,
    clinical_action TEXT NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (drug_a_id) REFERENCES drugs(drug_id) ON DELETE CASCADE,
    FOREIGN KEY (drug_b_id) REFERENCES drugs(drug_id) ON DELETE CASCADE,
    CHECK (drug_a_id < drug_b_id),
    UNIQUE (drug_a_id, drug_b_id)
);

CREATE INDEX IF NOT EXISTS idx_ddi_drug_a ON drug_interactions(drug_a_id);
CREATE INDEX IF NOT EXISTS idx_ddi_drug_b ON drug_interactions(drug_b_id);

CREATE TABLE IF NOT EXISTS contraindications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id INTEGER NOT NULL,
    contraindication_type TEXT NOT NULL,
    trigger_value TEXT NOT NULL,
    severity TEXT NOT NULL,
    reason TEXT NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (drug_id) REFERENCES drugs(drug_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_contra_drug_id ON contraindications(drug_id);
CREATE INDEX IF NOT EXISTS idx_contra_type ON contraindications(contraindication_type);

-- Layer 3: Session Audit & Telemetry (Optional V1)
CREATE TABLE IF NOT EXISTS recommendation_audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    queried_condition TEXT NOT NULL,
    candidate_count INTEGER NOT NULL,
    recommended_count INTEGER NOT NULL,
    filtered_count INTEGER NOT NULL,
    execution_time_ms REAL NOT NULL
);
"""


def _apply_schema_migrations(conn: sqlite3.Connection):
    """
    Applies non-destructive schema migrations for existing databases.
    """
    cursor = conn.cursor()
    # Check existing columns in drugs table
    cursor.execute("PRAGMA table_info(drugs);")
    existing_drug_cols = {col[1] for col in cursor.fetchall()}

    columns_to_add = [
        ("composition", "TEXT"),
        ("manufacturer", "TEXT"),
        ("price_inr", "REAL DEFAULT 0.0"),
        ("dosage_form", "TEXT DEFAULT 'Not specified'"),
        ("pack_size", "TEXT"),
        ("is_discontinued", "INTEGER DEFAULT 0"),
    ]
    for col_name, col_def in columns_to_add:
        if col_name not in existing_drug_cols:
            try:
                cursor.execute(f"ALTER TABLE drugs ADD COLUMN {col_name} {col_def};")
            except sqlite3.OperationalError:
                pass

    # Check existing columns in drug_conditions table
    cursor.execute("PRAGMA table_info(drug_conditions);")
    existing_dc_cols = {col[1] for col in cursor.fetchall()}
    dc_cols_to_add = [
        ("indication_type", "TEXT DEFAULT 'Primary'"),
        ("evidence_source", "TEXT DEFAULT 'Clinical Literature'"),
    ]
    for col_name, col_def in dc_cols_to_add:
        if col_name not in existing_dc_cols:
            try:
                cursor.execute(f"ALTER TABLE drug_conditions ADD COLUMN {col_name} {col_def};")
            except sqlite3.OperationalError:
                pass

    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_drugs_manufacturer ON drugs(manufacturer);")
    except sqlite3.OperationalError:
        pass

    conn.commit()


def init_db(db_path: Path | str | None = None) -> sqlite3.Connection:
    """
    Initializes SQLite database and creates tables if they do not exist.
    Enforces foreign key constraints and applies non-destructive migrations.
    """
    if db_path is None:
        db_path = settings.DATABASE_PATH

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")
    _apply_schema_migrations(conn)
    conn.executescript(SCHEMA_SQL)
    _apply_schema_migrations(conn)
    conn.commit()
    return conn


def get_db_connection(db_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Yields an SQLite connection with row factory enabled and foreign keys enforced.
    """
    if db_path is None:
        db_path = settings.DATABASE_PATH

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
