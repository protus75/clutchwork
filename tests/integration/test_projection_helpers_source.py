import ast
import re
from pathlib import Path


def ticket_index(node):
    return (isinstance(node, ast.Attribute) and node.attr == "ticket") or (isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value == "ticket")


def violations(path, source):
    tree = ast.parse(source)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    errors = []
    for node in ast.walk(tree):
        ancestors = []
        parent = parents.get(node)
        while parent is not None:
            ancestors.append(parent)
            parent = parents.get(parent)
        functions = [n.name for n in ancestors if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        owner = functions[0] if functions else ""
        bad = False
        if (
            isinstance(node, ast.Call)
            and path.name != "daemon.py"
            and ((isinstance(node.func, ast.Name) and node.func.id == "storm_producer") or (isinstance(node.func, ast.Attribute) and node.func.attr == "storm_producer"))
        ):
            bad = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "EngineLog" and not (path.name == "enginelog.py" and owner == "engine_log"):
                bad = True
            if node.func.id == "SimpleNamespace" and path.name == "observe.py" and owner != "as_events" and any(k.arg == "type" for k in node.keywords):
                bad = True
            if (
                node.func.id == "sum"
                and not (path.name == "journal.py" and owner == "total_spend")
                and any(isinstance(n, ast.Constant) and n.value == "usd" for arg in node.args for n in ast.walk(arg))
            ):
                bad = True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            if isinstance(node.right, ast.Constant) and node.right.value == "box":
                bad = True
            if path.name != "tickets.py" and not (isinstance(parents.get(node), ast.BinOp) and isinstance(parents[node].op, ast.Div)):
                parts = [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
                if "tickets" in parts and "ticket.md" in parts:
                    bad = True
        if path.name != "tickets.py" and isinstance(node, ast.JoinedStr) and re.search(r"tickets/\{[^}]+\}/ticket\.md", ast.unparse(node)):
            bad = True
        if path.name != "enginelog.py" and isinstance(node, ast.Constant) and isinstance(node.value, str) and "engine.log" in node.value:
            bad = True
        if path.name != "tickets.py" and isinstance(node, (ast.JoinedStr, ast.BinOp)):
            source_text = ast.unparse(node)
            names = ("run.md", "review.md", "checks.json", "diagnosis.json", "rework.md", "harvest.json")
            if any(name in source_text for name in names) and ("tickets" in source_text or "TICKETS_DIR" in source_text or "ticket_root" in source_text):
                bad = True
        if path.name in {"observe.py", "__main__.py"}:
            if isinstance(node, ast.DictComp) and ticket_index(node.key):
                bad = True
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(t, ast.Subscript) and ticket_index(t.slice) for t in targets):
                    bad = True
        if bad:
            errors.append(node.lineno)
    return errors


def test_projection_owners():
    root = Path(__file__).resolve().parents[2] / "clutch"
    errors = [f"{path.relative_to(root)}:{line}" for path in root.rglob("*.py") for line in violations(path, path.read_text())]
    assert not errors, ", ".join(errors)


def test_scan_rejects_copies_and_permits_exclusions():
    cases = [
        ("other.py", "storm_producer(root=r, fs=f, journal=j, clock=c)", True),
        ("other.py", "daemon.storm_producer(root=r, fs=f, journal=j, clock=c)", True),
        ("daemon.py", "storm_producer(root=r, fs=f, journal=j, clock=c)", False),
        ("daemon.py", "daemon.storm_producer(root=r, fs=f, journal=j, clock=c)", False),
        ("other.py", "EngineLog(p, r, c)", True),
        ("enginelog.py", "def engine_log():\n    EngineLog(p, r, c)", False),
        ("driver.py", "class Driver:\n    def from_config():\n        EngineLog(p, r, c)", True),
        ("other.py", 'state / "engine.log"', True),
        ("enginelog.py", 'state / "engine.log"', False),
        ("other.py", 'f"tickets/{stem}/run.md"', True),
        ("other.py", 'Path("tickets") / stem / "review.md"', True),
        ("other.py", 'ticket_root / "diagnosis.json"', True),
        ("other.py", 'f"{TICKETS_DIR}/{stem}/checks.json"', True),
        ("other.py", 'specs_dir / "rework.md"', False),
        ("tickets.py", 'f"tickets/{stem}/run.md"', False),
        ("other.py", 'p / "box"', True),
        ("other.py", 'f"tickets/{stem}/ticket.md"', True),
        ("other.py", 'Path("tickets") / stem / "ticket.md"', True),
        ("tickets.py", 'f"tickets/{stem}/ticket.md"', False),
        ("other.py", '(repo / "tickets").glob("*/ticket.md")', False),
        ("other.py", 'p / "ticket.md"', False),
        ("observe.py", '{e["ticket"]: e for e in events}', True),
        ("__main__.py", "{e.ticket: e for e in events}", True),
        ("observe.py", 'd[e["ticket"]] = e', True),
        ("__main__.py", "d[e.ticket] = e", True),
        ("observe.py", "SimpleNamespace(type=e.type)", True),
        ("observe.py", "def as_events():\n    SimpleNamespace(type=e.type)", False),
        ("other.py", 'sum(e["usd"] for e in events)', True),
        ("journal.py", 'def total_spend():\n    return sum(e["usd"] for e in events)', False),
        ("stats.py", 'surfaces[key] += cost["usd"]', False),
    ]
    for filename, source, rejected in cases:
        assert bool(violations(Path(filename), source)) is rejected, source
