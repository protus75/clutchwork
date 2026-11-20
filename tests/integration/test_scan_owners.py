# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test scan owners
# relates: []
# owner: engine
# verified: 96e46658
# hash: f18b26fd8651d139697ff4f15ad8891dbd8f3cef4d24b5a066a3aa8277d51e74
import ast
from pathlib import Path


def compares(node, attr, value):
    for child in ast.walk(node):
        if isinstance(child, ast.Compare) and any(isinstance(op, ast.Eq) for op in child.ops):
            operands = [child.left, *child.comparators]
            if any(isinstance(x, ast.Attribute) and x.attr == attr for x in operands) and any(
                (isinstance(x, ast.Attribute) and x.attr == value) or (isinstance(x, ast.Constant) and x.value == value.lower()) for x in operands
            ):
                return True
    return False


def ticket_equality(node, attr):
    return any(
        isinstance(c, ast.Compare) and any(isinstance(op, ast.Eq) for op in c.ops) and any(isinstance(x, ast.Attribute) and x.attr == attr for x in [c.left, *c.comparators]) for c in ast.walk(node)
    )


def violations(path, source):
    tree = ast.parse(source)
    errors = []
    owners = {"stages.py": {"served_review"}, "mergequeue.py": {"retained_ticket", "_finish"}, "merge.py": {"lifted_report_paths"}, "runner.py": {"apply_admission"}}
    for node in ast.walk(tree):
        if (
            path.name not in {"journal.py", "status.py"}
            and isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "next"
            and node.args
            and isinstance(node.args[0], ast.GeneratorExp)
        ):
            gen = node.args[0]
            if (
                any(isinstance(g.iter, ast.Call) and isinstance(g.iter.func, ast.Name) and g.iter.func.id == "reversed" for g in gen.generators)
                and compares(gen, "type", "STATE_TRANSITION")
                and ticket_equality(gen, "ticket")
                and not any(isinstance(x, ast.Name) and x.id == "TERMINAL_STATES" for x in ast.walk(gen))
            ):
                errors.append(node.lineno)
        if (
            path.name != "status.py"
            and isinstance(node, ast.DictComp)
            and isinstance(node.key, ast.Attribute)
            and node.key.attr == "ticket"
            and isinstance(node.value, ast.Subscript)
            and isinstance(node.value.value, ast.Attribute)
            and node.value.value.attr == "body"
            and isinstance(node.value.slice, ast.Constant)
            and node.value.slice.value == "to"
        ):
            errors.append(node.lineno)
    for func in (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in owners.get(path.name, set())):
        for node in ast.walk(func):
            if isinstance(node, (ast.ListComp, ast.GeneratorExp)) and compares(node, "type", "EFFECT_COMPLETION") and ticket_equality(node, "key"):
                errors.append(node.lineno)
    return errors


def test_scans_have_single_owners():
    root = Path(__file__).resolve().parents[2] / "clutch"
    errors = [f"{path.name}:{line}" for path in root.glob("*.py") for line in violations(path, path.read_text())]
    assert not errors, ", ".join(errors)
