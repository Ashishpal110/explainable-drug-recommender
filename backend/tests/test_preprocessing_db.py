"""
Unit tests for data preprocessing and Layer 1 database seeding.
"""

import sqlite3
import pytest
from pathlib import Path
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


def test_html_entity_decoding():
    assert decode_html_entities("It&#039;s effective &amp; cheap") == "It's effective & cheap"
    assert decode_html_entities("&quot;Great drug&quot;") == '"Great drug"'
    assert decode_html_entities("") == ""
    assert decode_html_entities(None) == ""


def test_clean_review_text():
    raw_text = 'It&#039;s a <br>good</br> medication. It did not cause nausea.\\r\\n'
    cleaned = clean_review_text(raw_text)
    assert "It's" in cleaned
    assert "<br>" not in cleaned
    assert "not cause nausea" in cleaned
    assert "\r" not in cleaned


def test_is_valid_condition():
    assert is_valid_condition("Hypertension") is True
    assert is_valid_condition("Type 2 Diabetes") is True
    assert is_valid_condition(None) is False
    assert is_valid_condition("nan") is False
    assert is_valid_condition("3</span> users found this comment helpful.") is False
    assert is_valid_condition("<span>something</span>") is False


def test_normalize_names():
    assert normalize_condition_name("  Hypertension   ") == "Hypertension"
    assert normalize_drug_name(' "Valsartan" ') == "Valsartan"
    assert normalize_drug_name("Ethinyl estradiol / norethindrone") == "Ethinyl estradiol / norethindrone"


def test_sentiment_proxy_labels():
    # Rating >= 7 -> Positive
    assert get_sentiment_proxy_label(10.0) == "Positive"
    assert get_sentiment_proxy_label(7.0) == "Positive"
    assert get_sentiment_proxy_int(7.0) == 1

    # Rating in [5, 6] -> Neutral
    assert get_sentiment_proxy_label(6.0) == "Neutral"
    assert get_sentiment_proxy_label(5.0) == "Neutral"
    assert get_sentiment_proxy_int(5.5) == 0

    # Rating <= 4 -> Negative
    assert get_sentiment_proxy_label(4.0) == "Negative"
    assert get_sentiment_proxy_label(1.0) == "Negative"
    assert get_sentiment_proxy_int(1.0) == -1


def test_database_initialization_and_constraints(tmp_path: Path):
    db_file = tmp_path / "test_drug_system.db"
    conn = init_db(db_file)
    cursor = conn.cursor()

    # Verify tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert "drugs" in tables
    assert "conditions" in tables
    assert "drug_conditions" in tables

    # Insert test drug
    cursor.execute(
        """
        INSERT INTO drugs (name, avg_rating, total_reviews, positive_sentiment_ratio)
        VALUES (?, ?, ?, ?)
        """,
        ("TestDrugA", 8.5, 10, 0.9),
    )
    drug_id = cursor.lastrowid

    # Test UNIQUE constraint on drugs.name
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO drugs (name, avg_rating, total_reviews, positive_sentiment_ratio)
            VALUES (?, ?, ?, ?)
            """,
            ("TestDrugA", 7.0, 5, 0.8),
        )

    # Insert test condition
    cursor.execute(
        "INSERT INTO conditions (name, category) VALUES (?, ?)",
        ("TestConditionA", "General"),
    )
    cond_id = cursor.lastrowid

    # Insert valid drug_condition mapping
    cursor.execute(
        """
        INSERT INTO drug_conditions (drug_id, condition_id, review_count, avg_rating)
        VALUES (?, ?, ?, ?)
        """,
        (drug_id, cond_id, 10, 8.5),
    )

    # Test UNIQUE constraint on (drug_id, condition_id)
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO drug_conditions (drug_id, condition_id, review_count, avg_rating)
            VALUES (?, ?, ?, ?)
            """,
            (drug_id, cond_id, 5, 7.0),
        )

    # Test Foreign Key constraint (non-existent drug_id)
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """
            INSERT INTO drug_conditions (drug_id, condition_id, review_count, avg_rating)
            VALUES (?, ?, ?, ?)
            """,
            (99999, cond_id, 1, 5.0),
        )

    conn.close()


def test_seeded_production_database():
    from app.core.config import settings
    db_path = settings.DATABASE_PATH
    assert db_path.exists(), f"Database not found at {db_path}"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM drugs;")
    drug_count = cursor.fetchone()[0]
    assert drug_count > 3000

    cursor.execute("SELECT COUNT(*) FROM conditions;")
    cond_count = cursor.fetchone()[0]
    assert cond_count > 700

    cursor.execute("SELECT COUNT(*) FROM drug_conditions;")
    dc_count = cursor.fetchone()[0]
    assert dc_count > 7000

    # Ensure no orphan foreign keys
    cursor.execute(
        """
        SELECT COUNT(*) FROM drug_conditions dc
        LEFT JOIN drugs d ON dc.drug_id = d.drug_id
        LEFT JOIN conditions c ON dc.condition_id = c.condition_id
        WHERE d.drug_id IS NULL OR c.condition_id IS NULL;
        """
    )
    orphans = cursor.fetchone()[0]
    assert orphans == 0

    conn.close()
