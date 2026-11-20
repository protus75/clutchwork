# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test seams rusage
# relates: [clutch/evidence/schema.py, clutch/seams.py]
# owner: engine
# verified: 9a610809
# hash: 6a68ac9d2643f0dfed89b8d5fc00411136aca04e28160dd06bba06e68ba6c499
from types import SimpleNamespace

from clutch.evidence.schema import Rusage
from clutch.seams import reap_outcome, rusage_figures


def test_rusage_and_reap_outcomes():
    ru = SimpleNamespace(ru_utime=1.5, ru_stime=0.25, ru_maxrss=20480)
    expected = Rusage(user_s=1.5, sys_s=0.25, max_rss_kb=20480)
    assert rusage_figures(ru) == expected
    received = []
    assert reap_outcome(3 << 8, ru, received.append) == 3
    assert received == [expected]
    assert reap_outcome(9, ru, None) == -9
    assert received == [expected]
