"""Unfinished implementation is a failed attempt, not a ticket defect."""

import pytest
from pydantic import ValidationError

from chupa.caps import failed_attempt
from chupa.stages import ImplementReply


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
