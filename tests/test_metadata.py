import os
import sys
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from metadata_utils import calculate_empathy_score, extract_emotional_intensity


@pytest.mark.parametrize(
    "text,expected_range",
    [
        ("I understand how you feel and I am here to support you.", (0.0, 1.0)),
        ("This is terrible and I hate everything.", (0.0, 1.0)),
    ],
)
def test_calculate_empathy_score(text, expected_range):
    score = calculate_empathy_score(text)
    assert isinstance(score, float)
    assert expected_range[0] <= score <= expected_range[1]


@pytest.mark.parametrize(
    "text,expected_range",
    [
        ("I am very happy today!", (0.0, 1.0)),
        ("I feel so bad and sad.", (0.0, 1.0)),
    ],
)
def test_extract_emotional_intensity(text, expected_range):
    intensity = extract_emotional_intensity(text)
    assert isinstance(intensity, float)
    assert expected_range[0] <= intensity <= expected_range[1]
