# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify total panel verdict tie orders.
# relates: [clutch/artifacts.py, clutch/panel.py, clutch/triage.py]
# owner: engine
# verified: d262e447
# hash: 8cc6cf21a18ed98526a1c0d2c2cb450f0901314aa25250d91ce5c59d288b9065
from itertools import combinations
from typing import get_args

import pytest

from clutch.artifacts import DiagnosisReply, DiagnosisVerdictName
from clutch.panel import DIAGNOSIS_ORDER, TRIAGE_ORDER, PanelMember, majority_verdict
from clutch.triage import TriageReply


def test_orders_and_ties():
    assert len(DIAGNOSIS_ORDER) == 5 and set(DIAGNOSIS_ORDER) == set(get_args(DiagnosisVerdictName))
    assert len(TRIAGE_ORDER) == 3 and set(TRIAGE_ORDER) == set(get_args(TriageReply.model_fields["verdict"].annotation))
    for order, factory in (
        (DIAGNOSIS_ORDER, lambda v: DiagnosisReply(verdict=v, lessons=["lesson"])),
        (TRIAGE_ORDER, lambda v: TriageReply(verdict=v, link="decision" if v == "tombstone" else None, summary="s", rationale="r", evidence=[], reopen_after_days=None if v == "author" else 1)),
    ):
        for n in range(2, min(3, len(order)) + 1):
            for values in combinations(order, n):
                replies = [factory(v) for v in reversed(values)]
                members = [PanelMember(provider="p", model="m", verdict=r.verdict) for r in replies]
                assert majority_verdict(replies, order, members)[0].verdict == values[0]
    assert DIAGNOSIS_ORDER.index("escalate") < DIAGNOSIS_ORDER.index("retry")
    assert TRIAGE_ORDER.index("declined") < TRIAGE_ORDER.index("author")
    replies = [DiagnosisReply(verdict=v, lessons=["x"]) for v in ("retry", "split")]
    with pytest.raises(ValueError):
        majority_verdict(replies, ("retry",), [PanelMember(provider="p", model="m", verdict=r.verdict) for r in replies])
