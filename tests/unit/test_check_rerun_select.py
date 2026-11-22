# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that the testreport pytest plugin deselects tests missing from the selection file, and that Check's rerun passes that file to the suite command.
# relates: [clutch/testreport.py, tests/unit/test_check_rerun_failed_only.py]
# owner: engine
# verified: fd407c31
# hash: 3aa47fa2bed2b06b2c1852b001851f07ad2736308dd3ec000edd7bd44f76e789
import json
from types import SimpleNamespace as NS

from clutch import testreport
from tests.unit.test_check_rerun_failed_only import run_check


def test_selection_and_rerun(tmp_path, monkeypatch):
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(["two"]))
    items = [NS(nodeid="one"), NS(nodeid="two")]
    removed = []
    testreport.pytest_collection_modifyitems(NS(getoption=lambda option: str(path), hook=NS(pytest_deselected=lambda items: removed.extend(items))), items)
    assert [item.nodeid for item in items] == ["two"]
    assert [item.nodeid for item in removed] == ["one"]
    _, calls, _, selections, _, _ = run_check(tmp_path, monkeypatch, [(1, {"two": "failed", "one": "passed"}), (1, {"two": "failed"})])
    assert calls[1] == ["test", "suite", "--clutch-select", str(tmp_path / "results.select.json")]
    assert selections == [["two"]]
