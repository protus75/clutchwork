"""Unfinished implementation is a failed attempt, not a ticket defect."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unfinished implementation is a failed attempt, not a ticket defect.
# relates: [clutch/caps.py, clutch/stages.py]
# owner: engine
# verified: 0a308920
# hash: 302783ce7ab7b1f7c9a29cae066f7aeca3c706c12ffa1b1091973010f0be4790

import pytest
from pydantic import ValidationError

from clutch.caps import failed_attempt
from clutch.stages import ImplementReply


def test_incomplete_reply_shape():
    reply = {"outcome": "incomplete", "summary": "stopped", "surprises": "none", "dead_ends": "none", "predicted_vs_actual": "none", "findings": []}
    assert ImplementReply.model_validate(reply).outcome == "incomplete"  # Rejecting the new outcome loses the retry.
    finding = {"code": "premise", "path": "ticket.md", "message": "contradiction", "paved_road": "correct ticket"}
    for outcome in ("incomplete", "ok"):
        with pytest.raises(ValidationError):  # Accepting findings would misclassify a ticket defect.
            ImplementReply.model_validate({**reply, "outcome": outcome, "findings": [finding]})


def test_incomplete_is_a_failed_attempt():
    assert failed_attempt({"to": "incomplete", "stage": "implement"})  # Omitting incomplete bypasses the cap.
    assert not failed_attempt({"to": "already_satisfied"})  # Counting success spends the cap.
