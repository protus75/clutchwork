# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify stage panel call site structure.
# relates: [clutch/stages.py, clutch/panel.py]
# owner: engine
# verified: d262e447
# hash: a2607faf03da382827c7028f85908b97f2b73f29f4ecf914c92d86f1d2ddc35a
import ast
from pathlib import Path


def test_panel_call_sites():
    tree = ast.parse((Path(__file__).resolve().parents[2] / "clutch/stages.py").read_text())
    for name in ("diagnose", "review"):
        fn = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
        calls = [ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)]
        assert calls.count("ctx.driver.run") == 1
        assert calls.count("ctx.driver.run_panel") == 1
        assert calls.count("_panel_combine") == 1
        assert not any(isinstance(n, ast.Call) and ast.unparse(n.func) == "sum" and ".usd" in ast.unparse(n) for n in ast.walk(fn))
    assert sum(isinstance(n, ast.Call) and ast.unparse(n.func) == "_panel_combine" for n in ast.walk(tree)) == 2
