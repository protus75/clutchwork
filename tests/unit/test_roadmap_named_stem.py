from clutch.roadmap import fresh_stem


def test_fresh_stem_uses_first_available_suffix():
    assert fresh_stem("supervise-idle-point", {"supervise-idle-point"}) == "supervise-idle-point-r1"
    assert fresh_stem("x-r1", {"x", "x-r1"}) == "x-r2"
