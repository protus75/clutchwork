# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify triage panel call site structure.
# relates: []
# owner: engine
# verified: b1bfcbf6
# hash: 60b1bf5ef1705459491efe37d3f1538a2a3ba7634b3ea52f465b4b70fd31c63a
import ast
from pathlib import Path


def test_panel_call_sites():
    tree = ast.parse((Path(__file__).resolve().parents[2] / "clutch/triage.py").read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "_settle_pass")
    calls = [ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)]
    # Wrong: duplicating driver calls or panel bookkeeping.
    assert calls.count("driver.run") == calls.count("driver.run_panel") == calls.count("_panel_combine") == 1
    assert sum(isinstance(n, ast.Call) and ast.unparse(n.func) == "_panel_combine" for n in ast.walk(tree)) == 1
    assert not any(isinstance(n, ast.Call) and ast.unparse(n.func) == "sum" and ".usd" in ast.unparse(n) for n in ast.walk(fn))
