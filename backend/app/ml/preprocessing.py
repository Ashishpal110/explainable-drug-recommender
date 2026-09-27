"""
Preprocessing module for drug review text and medical conditions.
"""

import html
import re
from typing import Optional


def decode_html_entities(text: str) -> str:
    """
    Decodes HTML entities (e.g., &#039; -> ', &amp; -> &, &quot; -> ").
    """
    if not isinstance(text, str):
        return ""
    # Double unescape in case of doubly encoded entities
    return html.unescape(html.unescape(text))


def clean_review_text(text: str) -> str:
    """
    Cleans unstructured patient review text:
    - Decodes HTML entities
    - Removes residual HTML tags (e.g. <br>, <p>, <span>)
    - Normalizes quotes, dashes, and excess whitespace
    - Preserves negation tokens (not, no, never, without, etc.) and semantic punctuation
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    # Decode HTML
    cleaned = decode_html_entities(text)

    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    # Normalize weird quotation characters and backslashes
    cleaned = cleaned.replace('""', '"').replace('\\r\\n', ' ').replace('\\n', ' ').replace('\\r', ' ')
    cleaned = re.sub(r'[\u2018\u2019]', "'", cleaned)
    cleaned = re.sub(r'[\u201c\u201d]', '"', cleaned)

    # Normalize multiple whitespace characters
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def is_valid_condition(condition: Optional[str]) -> bool:
    """
    Validates whether a condition string is a legitimate medical indication
    rather than web artifact noise (e.g., '3</span> users found this comment helpful.').
    """
    if not condition or not isinstance(condition, str):
        return False

    cond_clean = condition.strip()
    if not cond_clean or cond_clean.lower() == "nan" or cond_clean.lower() == "null":
        return False

    # Check for HTML tags or 'users found' artifacts
    if re.search(r"<\s*/?\s*span", cond_clean, re.IGNORECASE):
        return False
    if re.search(r"users found this comment helpful", cond_clean, re.IGNORECASE):
        return False
    if re.search(r"^\d+\s*users\b", cond_clean, re.IGNORECASE):
        return False

    return True


def normalize_condition_name(condition: str) -> str:
    """
    Normalizes condition strings:
    - Decodes HTML entities
    - Strips whitespace
    - Formats consistently
    """
    if not isinstance(condition, str):
        return ""

    cond = decode_html_entities(condition).strip()
    # Normalize common casing and spacing
    cond = re.sub(r"\s+", " ", cond)
    return cond


def normalize_drug_name(drug_name: str) -> str:
    """
    Normalizes drug names without fabricating entities or merging distinct medications:
    - Decodes HTML entities
    - Strips surrounding quotes and whitespace
    """
    if not isinstance(drug_name, str):
        return ""

    name = decode_html_entities(drug_name).strip()
    # Strip enclosing quotes if present
    name = name.strip('"\'')
    return re.sub(r"\s+", " ", name)


def get_sentiment_proxy_label(rating: float) -> str:
    """
    Maps 10-point user review rating to a rating-derived proxy sentiment label:
      - Positive: rating >= 7
      - Neutral:  rating in [5, 6]
      - Negative: rating <= 4

    IMPORTANT: These are rating-derived proxy labels, NOT independently
    annotated clinical sentiment ground truth. They reflect patient satisfaction
    scores and do not establish pharmacological efficacy.
    """
    try:
        r = float(rating)
    except (ValueError, TypeError):
        return "Neutral"

    if r >= 7.0:
        return "Positive"
    elif r >= 5.0:
        return "Neutral"
    else:
        return "Negative"


def get_sentiment_proxy_int(rating: float) -> int:
    """
    Integer representation: Positive (1), Neutral (0), Negative (-1).
    """
    label = get_sentiment_proxy_label(rating)
    if label == "Positive":
        return 1
    elif label == "Neutral":
        return 0
    else:
        return -1
