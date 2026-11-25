"""Source shape guards and real CLI refusal paths for the shared verb plumbing."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the source shape of the shared verb plumbing in __main__ (each shared call has one owner) and the real CLI refusal paths
# relates: [clutch/__main__.py, clutch/lockfile.py, clutch/runner.py, tests/integration/test_cli.py]
# owner: clutch/__main__.py
# verified: 13ffeebe
# hash: 95c91db2296ec6f83add0f715610c37748495a6f450003828e1a2d56d936576f

import ast
import json
from pathlib import Path

import pytest

from clutch import __main__ as entry
from clutch import runner
from clutch.lockfile import Lockfile, LockHeld
from tests.cli_helpers import ENV, Clock, root

pytestmark = pytest.mark.disk_io_skip


def calls(node, owner=None):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        owner = node.name
    if isinstance(node, ast.Call):
        yield owner, node
    for child in ast.iter_child_nodes(node):
        yield from calls(child, owner)


@pytest.fixture
def source_tree():
    return ast.parse(Path(entry.__file__).read_text())


@pytest.mark.parametrize(
    ("module", "callee", "owners"),
    [
        (entry, "Lockfile", []),
        (entry, "_require_engine", []),
        (entry, "control.read_active", []),
        (entry, "control.publish_request", []),
        (entry, "observe.Context", ["_observe_context"]),
        (runner, "Lockfile", ["run_ticket", "verdict", "_locked"]),
        (runner, "_require_engine", ["submit_engine"]),
        (runner, "control.read_active", ["submit_engine"]),
        (runner, "control.publish_request", ["submit_engine"]),
    ],
)
def test_shared_call_has_one_owner(module, callee, owners):
    # A copied call site, or moving the sole call outside its owner, changes this list.
    tree = ast.parse(Path(module.__file__).read_text())
    assert [function for function, call in calls(tree) if ast.unparse(call.func) == callee] == owners


def test_config_reload_lambda_has_one_owner(source_tree):
    # Inline reload lambdas in any handler/constructor would add entries here.
    assert [
        owner for owner, call in calls(source_tree) if ast.unparse(call.func) == "load_config" and any(isinstance(node, ast.Lambda) and call in ast.walk(node) for node in ast.walk(source_tree))
    ] == ["_config_reloader"]


def test_stderr_prints_have_one_prefixed_owner(source_tree):
    # A handler printing a refusal itself adds a fourth site; the two unprefixed warnings stay.
    assert sorted(
        owner for owner, call in calls(source_tree) if ast.unparse(call.func) == "print" and any(keyword.arg == "file" and ast.unparse(keyword.value) == "sys.stderr" for keyword in call.keywords)
    ) == ["_fail", "handle_issue", "handle_probe"]


def test_prompt_box_refusal_is_caught(root, capsys):
    # Dispatch outside the exception boundary raises; dropping the road/prefix changes stderr.
    assert entry.main(["prompt", "box"], cwd=root, env=ENV, clock=Clock()) == runner.EXIT_REFUSED
    assert capsys.readouterr().err == "clutch prompt: box prompt requires ids -- name at least one box id\n"


def test_dismiss_names_holder_and_preserves_lock(root, capsys):
    state = root / ".clutch/state"
    lock = Lockfile(state, verb="triage", instance_id="integration-holder", clock=Clock())
    lock.acquire()
    try:
        expected = f"clutch box: {LockHeld(lock.path, json.loads(lock.path.read_text()))}\n"
        # Bypassing the wrapper or swallowing LockHeld cannot return this refusal.
        assert entry.main(["box", "dismiss", "box-000001"], cwd=root, env=ENV, clock=Clock()) == runner.EXIT_REFUSED
        assert capsys.readouterr().err == expected
        # A refused acquisition must not create another lock or remove the holder's file.
        assert list(state.rglob("*.lock")) == [lock.path]
    finally:
        lock.release()
