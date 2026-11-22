# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test checking that Driver.stage allows only same-stem review_visual and meta-stem meta stages inside a check stage, restores the outer stage, and rejects any nesting under other surfaces
# relates: [clutch/driver.py]
# owner: clutch/driver.py
# verified: ae8dbac1
# hash: 9f325a0d7a36fcdc8f4b226f61823d5231793f6dc9dd57729b963ec48c5399ae
from types import SimpleNamespace

import pytest

from clutch.driver import Driver


def test_check_nesting_restores_and_restricts():
    driver = Driver.__new__(Driver)
    driver._open_stage = None
    driver.log = SimpleNamespace(event=lambda *a, **kw: None)
    with driver.stage(stem="work", attempt=1, surface="check"):
        with driver.stage(stem="work", attempt=1, surface="review_visual"):
            assert driver._open_stage == ("work", "review_visual")
        assert driver._open_stage == ("work", "check")
        with driver.stage(stem="meta", attempt=1, surface="meta"):
            assert driver._open_stage == ("meta", "meta")
        assert driver._open_stage == ("work", "check")
        for stem, surface in [("work", "review"), ("other", "review_visual"), ("other", "meta"), ("meta", "review")]:
            with pytest.raises(ValueError, match="stage already open"), driver.stage(stem=stem, attempt=1, surface=surface):
                pass
    with driver.stage(stem="work", attempt=1, surface="implement"):
        with pytest.raises(ValueError, match="stage already open"), driver.stage(stem="meta", attempt=1, surface="meta"):
            pass
        with pytest.raises(ValueError, match="stage already open"), driver.stage(stem="work", attempt=1, surface="review_visual"):
            pass
    assert driver._open_stage is None
