# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test closed sets single owner
# relates: []
# owner: engine
# verified: 148a8874
# hash: 0856ac868af39e71391a15c71b3a752104a6a9ffa9e443fcbe6a11820796a182
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_single_definitions():
    owners = {"StrictModel": [], "FrozenModel": [], "NonBlank": [], "sha1": []}
    for path in (ROOT / "clutch").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in {"_Strict", "Strict"}, path
                if node.name in owners:
                    owners[node.name].append(path.name)
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(target, ast.Name) and target.id == "NonBlank" for target in targets):
                    owners["NonBlank"].append(path.name)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "hashlib" and node.func.attr == "sha1":
                owners["sha1"].append(path.name)
        if path.name in {"requisition.py", "rework.py", "policy.py", "baseline.py"}:
            assert not any(
                isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "split" and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "."
                for n in ast.walk(tree)
            ), path
    assert owners == {"StrictModel": ["artifacts.py"], "FrozenModel": ["artifacts.py"], "NonBlank": ["artifacts.py"], "sha1": ["git.py"]}


def test_closed_set_literals_have_one_home():
    for path in (ROOT / "clutch").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
                values = {item.value for item in node.elts if isinstance(item, ast.Constant) and isinstance(item.value, str)}
                if path.name != "llm.py":
                    assert values != {"low", "medium", "high", "max"}, path
                if path.name not in {"tickets.py", "author.py"}:
                    assert not {"feature", "bug", "chore"} <= values, path
                    assert not {"P0", "P1", "P2", "P3"} <= values, path
