# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that testreport.pytest_collection_modifyitems keeps only the test node IDs listed in the selection JSON file and reports the rest as deselected.
# relates: [clutch/testreport.py]
# owner: clutch/testreport.py
# verified: fd407c31
# hash: b9f8d145c319fb2dc8bf43a113c53d719a4fd88f98c1dcaf199fdee5890447b5
import json
from types import SimpleNamespace as NS

from clutch import testreport


def test_selection_deselects_unlisted(tmp_path):
    path = tmp_path / "select.json"
    path.write_text(json.dumps(["b"]))
    items = [NS(nodeid=node) for node in ("a", "b", "c")]
    deselected = []
    config = NS(getoption=lambda option: str(path), hook=NS(pytest_deselected=lambda items: deselected.extend(items)))
    testreport.pytest_collection_modifyitems(config, items)
    assert [item.nodeid for item in items] == ["b"]
    assert [item.nodeid for item in deselected] == ["a", "c"]
