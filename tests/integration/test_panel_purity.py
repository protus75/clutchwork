# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test panel purity
# relates: []
# owner: engine
# verified: 96e46658
# hash: cea0f0378913f3dfd0df5c08cc4f4c67218d606e8e4e421b6431524539bdfd29
import ast
from pathlib import Path


def test_panel_imports_and_access_are_pure():
    tree = ast.parse((Path(__file__).resolve().parents[2] / "clutch/panel.py").read_text())
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert imports == {"collections", "typing", "pydantic", "clutch.artifacts"}
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"open", "exec", "eval", "__import__"} for node in ast.walk(tree))
