# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test driver check nesting
# relates: [clutch/driver.py]
# owner: clutch/driver.py
# verified: 0a308920
# hash: fb503b2eae8c66a1a46b6f2ccf8b15ef03b15647ba91bea63f5c09b4ac53fab1
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
        for stem, surface in [("work", "review"), ("other", "review_visual")]:
            with pytest.raises(ValueError, match="stage already open"), driver.stage(stem=stem, attempt=1, surface=surface):
                pass
    with driver.stage(stem="work", attempt=1, surface="implement"):
        with pytest.raises(ValueError, match="stage already open"), driver.stage(stem="work", attempt=1, surface="review_visual"):
            pass
    assert driver._open_stage is None
