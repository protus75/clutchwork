# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Check capture ownership and spool path removal.
# relates: []
# owner: engine
# verified: 23d3b116
# hash: b78942b1f1d371953535cab71e6a9a24be0b993312bc88ccbff1e45876603894
import ast
from pathlib import Path


def test_spool_paths_and_capture_key_owner():
    root = Path(__file__).resolve().parents[2] / "clutch"
    calls = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert "spools" not in node.value.split("/")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "capture_key":
                calls.append(path.relative_to(root).as_posix())
    assert calls == ["driver.py"]
