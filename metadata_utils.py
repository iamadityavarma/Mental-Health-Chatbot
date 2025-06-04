from __future__ import annotations
import math
import re
from typing import List, Dict

POSITIVE_WORDS = {
    "good", "great", "love", "happy", "joy", "awesome", "excellent", "positive",
    "support", "care", "compassion", "understand", "empathize",
}
NEGATIVE_WORDS = {
    "bad", "sad", "hate", "angry", "depressed", "anxious", "negative", "upset",
    "pain", "hurt", "worst",
}

EMPATHY_KEYWORDS = {
    "understand", "feel", "support", "care", "listen",
    "compassion", "validate", "comfort", "empathize",
}


def _simple_sentiment(text: str) -> Dict[str, float]:
    words = re.findall(r"\b\w+\b", text.lower())
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = len(words) or 1
    compound = (pos - neg) / max(pos + neg, 1)
    return {
        "compound": compound,
        "pos": pos / total,
        "neg": neg / total,
    }


def calculate_empathy_score(response: str) -> float:
    sentiment = _simple_sentiment(response)

    keyword_count = sum(1 for word in EMPATHY_KEYWORDS if word in response.lower())

    sentences = [s.strip() for s in re.split(r"[.!?]+", response) if s.strip()]
    if sentences:
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
    else:
        avg_sentence_length = len(response.split())

    empathy_score = (
        (sentiment["compound"] + 1) / 2
        * (1 + math.log(keyword_count + 1))
        * (1 / (1 + abs(avg_sentence_length - 10)))
    )
    return round(float(empathy_score), 2)


def extract_emotional_intensity(text: str) -> float:
    sentiment = _simple_sentiment(text)
    emotional_intensity = abs(sentiment["compound"]) * (sentiment["pos"] + sentiment["neg"])
    return round(float(emotional_intensity), 2)
