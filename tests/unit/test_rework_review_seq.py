# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify rework review effect sequence selection.
# relates: [clutch/rework.py]
# owner: clutch/rework.py
# verified: 5110a5cc
# hash: 0d39100a872bad30af99f618a1300207497e48d093ac6293da791816a2384940
from types import SimpleNamespace

from clutch.rework import next_review_seq


def test_sequence_families_and_identity():
    def seq(*keys):
        return next_review_seq([SimpleNamespace(key=k) for k in keys], "t", 2, 2)

    assert seq() == 0
    assert seq("llm/t/2/requisition_review/2/1", "llm/t/2/requisition_review/2/2") == 2
    assert seq("llm/t/m0-2/requisition_review/2/1", "llm/t/m1-2/requisition_review/2/1") == 1
    assert seq("llm/t/2/requisition_review/2/2", "llm/t/m1-2/requisition_review/2/4") == 4
    assert seq("llm/t/m0-12/requisition_review/2/5", "llm/u/m0-2/requisition_review/2/6", "llm/t/m0-2/requisition_review/3/7") == 0
