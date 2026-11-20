"""Diagnosis lesson normalization preserves all other schema checks."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Diagnosis lesson normalization preserves all other schema checks.
# relates: [clutch/artifacts.py]
# owner: clutch/artifacts.py
# verified: 0a308920
# hash: 67b4d05ca5d8ced08e1e8bb8a6ee4480eaa1409fa5a005e9dd49e4755fbf5822

import pytest
from pydantic import ValidationError

from clutch.artifacts import DiagnosisReply


def reply(lessons, **extra):
    return DiagnosisReply.model_validate({"verdict": "retry", "lessons": lessons, **extra})


@pytest.mark.parametrize("length", [324, 306, 343, 331, 303])
def test_word_boundary(length):
    # Use complete five-character words with a distinct overrun suffix.
    text = ("words  " + "words " * 60)[:length]
    assert len(text) == length
    result = reply([text])
    assert result.lessons == ["words  " + " ".join(["words"] * 48)]
    assert result.trimmed_lessons == [0]


def test_no_whitespace_and_limits():
    result = reply(["x" * 400, "y" * 300, "z" * 299])
    assert result.lessons == ["x" * 300, "y" * 300, "z" * 299]
    assert result.trimmed_lessons == [0]
    assert reply(["y" * 300, "z" * 299]).trimmed_lessons == []


def test_only_middle_and_supplied_indexes():
    result = reply(["a" * 100, "b" * 320, "c" * 100])
    assert result.lessons == ["a" * 100, "b" * 300, "c" * 100]
    assert result.trimmed_lessons == [1]
    assert reply(["short"], trimmed_lessons=[9]).trimmed_lessons == []


def test_surrounding_whitespace():
    result = reply([" " * 300 + "x" * 100, " " + "x" * 399])
    assert result.lessons == ["x" * 100, "x" * 300]
    assert result.trimmed_lessons == [1]


@pytest.mark.parametrize(
    "value",
    [
        {"verdict": "maybe", "lessons": ["valid"]},
        {"verdict": "retry", "lessons": []},
        {"verdict": "retry", "lessons": ["   "]},
        {"verdict": "retry", "lessons": ["x"] * 6},
        {"verdict": "retry", "lessons": ["x"], "extra": 1},
        {"verdict": "retry", "lessons": [123]},
    ],
)
def test_other_violations_remain_invalid(value):
    with pytest.raises(ValidationError):
        DiagnosisReply.model_validate(value)
