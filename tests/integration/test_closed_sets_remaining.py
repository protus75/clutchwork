import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_single_definitions():
    for path in (ROOT / "clutch").glob("*.py"):
        source = path.read_text()
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and target.id in {"RETIRED", "CLOSED", "SETTLED"}:
                        assert path.name == "status.py", (path, target.id)
        if path.name != "status.py":
            assert 'SETTLED | {"rejected"}' not in source
            assert "SETTLED | RETIRED" not in source
        assert "- SETTLED - " not in source
        if path.name in {"stages.py", "artifacts.py"}:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name != "major":
                    assert '.split(".")[0]' not in ast.get_source_segment(source, node)
        if path.name == "retro.py":
            for node in tree.body:
                if isinstance(node, ast.ImportFrom):
                    assert not ({alias.name for alias in node.names} & {"CLOSED", "SETTLED"})


def test_no_import_cycle():
    for module in ("clutch.retro", "clutch.status"):
        result = subprocess.run([sys.executable, "-c", f"import {module}"], capture_output=True, text=True, cwd=ROOT, check=False)
        assert result.returncode == 0, result.stderr
