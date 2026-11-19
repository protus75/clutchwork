import pytest

from clutch.driver import unwrap_fence
from clutch.requisition import RequisitionReply


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('Verdict: approve.\n{"a": 1}', '{"a": 1}'),
        ('before {"a": 1} after', '{"a": 1}'),
        ('x {"a": 1} y {"b": 2}', 'x {"a": 1} y {"b": 2}'),
        ("no json here", "no json here"),
        ('see {not json} then {"a": {"b": 1}}', '{"a": {"b": 1}}'),
        ('result {"a": "} inside"} done', '{"a": "} inside"}'),
    ],
)
def test_extract_single_object(text, expected):
    assert unwrap_fence(text) == expected


def test_prose_reply_validates():
    text = 'Review: {"verdict":"approve","summary":"Looks good","findings":[]}'
    reply = RequisitionReply.model_validate_json(unwrap_fence(text))
    assert reply.verdict == "approve"
