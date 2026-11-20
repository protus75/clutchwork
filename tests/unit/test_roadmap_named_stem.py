# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test roadmap named stem
# relates: [clutch/roadmap.py]
# owner: clutch/roadmap.py
# verified: 9a610809
# hash: d2562ff3aaf06534e0189eb79e1a7df52575aeb6a5141ce6e43131398de96c77
from clutch.roadmap import fresh_stem


def test_fresh_stem_uses_first_available_suffix():
    assert fresh_stem("supervise-idle-point", {"supervise-idle-point"}) == "supervise-idle-point-r1"
    assert fresh_stem("x-r1", {"x", "x-r1"}) == "x-r2"
