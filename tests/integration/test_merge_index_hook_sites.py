"""The shared squash terminal owns the refresh hook."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: write_squash is the single index hook call site
# relates: []
# owner: engine
# verified: 8c543cf0
# hash: 9f4bd69cc2a7117f098e43cf894eb6dc704ab2de7ccf6eac43d255ffe0a5560e

import ast
from pathlib import Path


def test_hook_sites():
    root = Path(__file__).resolve().parents[2]
    tree = ast.parse((root / "clutch/merge.py").read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "refresh_index"]
    squash = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "write_squash")
    assert len(calls) == 1
    assert any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Await) and n.value.value is calls[0] for n in squash.body)
    queue = ast.parse((root / "clutch/mergequeue.py").read_text())
    assert not any(isinstance(n, ast.Name) and n.id in {"refresh_index", "index"} or isinstance(n, ast.Attribute) and n.attr in {"refresh_index", "index"} for n in ast.walk(queue))
    cls = next(n for n in queue.body if isinstance(n, ast.ClassDef) and n.name == "MergeQueue")
    sites = [
        (fn.name, n)
        for fn in cls.body
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
        for n in ast.walk(fn)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == "merge" and n.func.attr == "write_squash"
    ]
    assert sorted(name for name, _ in sites) == ["_admit", "_finish"]
