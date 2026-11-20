import ast
from pathlib import Path


def test_panel_imports_and_access_are_pure():
    tree = ast.parse((Path(__file__).resolve().parents[2] / "clutch/panel.py").read_text())
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert imports == {"collections", "typing", "pydantic", "clutch.artifacts"}
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"open", "exec", "eval", "__import__"} for node in ast.walk(tree))
