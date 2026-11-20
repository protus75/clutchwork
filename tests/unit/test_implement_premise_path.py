"""Implement premise failures must identify the affected file."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Implement premise failures must identify the affected file.
# relates: [clutch/stages.py]
# owner: clutch/stages.py
# verified: 0a308920
# hash: e965f37342ee3939598a7981f95b049d7a00c5f20e4fc7d42e190f5299dbc018

import pytest
from pydantic import ValidationError

from clutch.stages import ImplementReply


def test_premise_findings_need_paths():
    reply = {
        "outcome": "premise_failed",
        "summary": "blocked",
        "surprises": "none",
        "dead_ends": "none",
        "predicted_vs_actual": "none",
        "findings": [{"code": "premise", "path": None, "message": "contradiction", "paved_road": "correct ticket"}],
    }
    with pytest.raises(ValidationError) as exc:
        ImplementReply.model_validate(reply)
    assert "naming `path`" in str(exc.value)
    assert "implement the ticket" in str(exc.value)

    reply["findings"][0]["path"] = "tickets/example/ticket.md"
    assert ImplementReply.model_validate(reply).findings[0].path == "tickets/example/ticket.md"
    reply["findings"][0]["path"] = " "
    with pytest.raises(ValidationError):
        ImplementReply.model_validate(reply)
    reply["outcome"] = "ok"
    reply["findings"] = []
    assert ImplementReply.model_validate(reply).outcome == "ok"
