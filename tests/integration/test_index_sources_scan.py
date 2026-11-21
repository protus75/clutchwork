# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Enforce the index source write and import boundaries.
# relates: []
# owner: engine
# verified: 8c543cf0
# hash: 75ab41fb7f9c3722c7b8735642087fd08add1714b2eb2a2d56d90792e775f803
import ast
from pathlib import Path


def test_source_write_and_import_boundaries():
    tree = ast.parse((Path(__file__).resolve().parents[2] / "clutch/index.py").read_text())
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_write_entry")
    inserts = [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and "INSERT INTO files" in n.value]
    assert len(inserts) == 1 and inserts[0] in ast.walk(helper)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_write_entry"]
    assert len(calls) == 3
    forbidden = {"roadmap", "runner", "author", "merge", "mergequeue"}
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert not any(alias.name in {f"clutch.{name}" for name in forbidden} for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module not in {f"clutch.{name}" for name in forbidden}
            assert node.module != "clutch" or not any(alias.name in forbidden for alias in node.names)
