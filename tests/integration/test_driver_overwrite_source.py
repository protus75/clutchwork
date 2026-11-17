from pathlib import Path

import pytest


@pytest.mark.parametrize("name", ["runner.py", "triage.py", "__main__.py"])
@pytest.mark.parametrize("assignment", ["driver.journal = ", "driver.effects = "])
def test_driver_journal_is_not_overwritten(name, assignment):
    source = (Path(__file__).resolve().parents[2] / "clutch" / name).read_text()
    assert assignment not in source
