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
