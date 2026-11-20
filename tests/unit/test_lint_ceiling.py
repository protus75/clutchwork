# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test lint ceiling
# relates: [clutch/__main__.py]
# owner: clutch/__main__.py
# verified: 0a308920
# hash: 3733d2e8af4b7e931694403a4be1b927ee50099ae534f8834f92f12d45539a2b
from clutch.__main__ import stuck_ceiling_finding


def test_stuck_over_ceiling_finding():
    finding = stuck_ceiling_finding(91, 90)
    assert finding is not None
    assert "91m" in finding and "90m" in finding
    assert "lower `- stuck:`" in finding and "split" in finding
    assert stuck_ceiling_finding(90, 90) is None
