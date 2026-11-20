# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test visual select
# relates: [clutch/visual.py]
# owner: clutch/visual.py
# verified: 9a610809
# hash: e703d05ac4d5df2386e5c285515057625ca933a47c2fa25b1ec8eb9e2c829143
from clutch.visual import decide, rank


def test_decision_margin_and_uncertainty():
    accept = (2, "accept", 4, 0.8, 5)
    assert decide([accept, (0, "reject", 3, 0.9, 9)]) == (2, None)
    assert decide([accept, (1, "accept", 4, 0.7, 4)]) == (None, "visual_undecided")
    assert decide([accept, (1, "unsure", 1, 0.7, 4)]) == (None, "visual_undecided")
    assert decide([accept]) == (2, None)
    assert decide([]) == (None, "visual_undecided")
    assert decide([(1, "reject", 4, 0.7, 4)]) == (None, "visual_undecided")


def test_rank_keys():
    candidates = [(0, "reject", 9, 1.0, 9), (1, "unsure", 9, 1.0, 9), (2, "accept", 1, 1.0, 9), (3, "accept", 2, 0.5, 1), (4, "accept", 2, 0.8, 1), (5, "accept", 2, 0.8, 2)]
    assert [c[0] for c in rank(candidates)] == [5, 4, 3, 2, 1, 0]
