# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test driver overwrite source
# relates: []
# owner: engine
# verified: 148a8874
# hash: 2a5fdef2f79cc76461afcef818ca2dd901e843d2344dc084e39d4707226e0478
from pathlib import Path

import pytest


@pytest.mark.parametrize("name", ["runner.py", "triage.py", "__main__.py"])
@pytest.mark.parametrize("assignment", ["driver.journal = ", "driver.effects = "])
def test_driver_journal_is_not_overwritten(name, assignment):
    source = (Path(__file__).resolve().parents[2] / "clutch" / name).read_text()
    assert assignment not in source
