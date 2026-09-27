from .preprocessing import (
    clean_review_text,
    decode_html_entities,
    is_valid_condition,
    normalize_condition_name,
    normalize_drug_name,
    get_sentiment_proxy_label,
    get_sentiment_proxy_int,
)
from .sentiment import SentimentModel
from .recommendation import ContentRecommender

# Backward compatibility alias
clean_text = clean_review_text

__all__ = [
    "clean_text",
    "clean_review_text",
    "decode_html_entities",
    "is_valid_condition",
    "normalize_condition_name",
    "normalize_drug_name",
    "get_sentiment_proxy_label",
    "get_sentiment_proxy_int",
    "SentimentModel",
    "ContentRecommender",
]
