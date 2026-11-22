"""Dispatch exceptions produce at most one terminal transition."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test that dispatch_exception_terminal journals an infra_error terminal only when the ticket is still running
# relates: [clutch/journal.py, clutch/runner.py, tests/fakes.py]
# owner: engine
# verified: 33066275
# hash: 7e8d01b8be457407ebf0aada66f4fcf12366727b975880e4fcc39e4e7c8ff088

import pytest

from clutch.journal import EventType
from clutch.runner import dispatch_exception_terminal
from tests.fakes import FakeJournal


@pytest.mark.parametrize("prior", ["running", "gate_failed"])
def test_dispatch_exception_terminal(prior):
    journal = FakeJournal()
    journal.append(EventType.STATE_TRANSITION, {"to": prior}, ticket="work")
    dispatch_exception_terminal(journal, "work", ValueError("boom"))
    expected = [{"to": prior}]
    if prior == "running":
        expected.append({"to": "infra_error", "stage": "dispatch", "reason": "dispatch_exception", "error": "ValueError: boom"})
    assert [event.body for event in journal.read()] == expected
