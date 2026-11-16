"""Source shape guards and real CLI refusal paths for the shared verb plumbing."""

import ast
import json
from pathlib import Path

import pytest

from clutch import __main__ as entry
from clutch import runner
from clutch.lockfile import Lockfile, LockHeld
from tests.integration.test_cli import ENV, Clock, root


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
    ("callee", "owner"),
    [
        ("Lockfile", "_locked"),
        ("_require_engine", "_submit_engine"),
        ("control.read_active", "_submit_engine"),
        ("control.publish_request", "_submit_engine"),
        ("observe.Context", "_observe_context"),
    ],
)
def test_shared_call_has_one_owner(source_tree, callee, owner):
    # A copied call site, or moving the sole call outside its owner, changes this list.
    assert [function for function, call in calls(source_tree) if ast.unparse(call.func) == callee] == [owner]


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
        expected = f"clutch dismiss: {LockHeld(lock.path, json.loads(lock.path.read_text()))}\n"
        # Bypassing the wrapper or swallowing LockHeld cannot return this refusal.
        assert entry.main(["dismiss", "box-000001"], cwd=root, env=ENV, clock=Clock()) == runner.EXIT_REFUSED
        assert capsys.readouterr().err == expected
        # A refused acquisition must not create another lock or remove the holder's file.
        assert list(state.rglob("*.lock")) == [lock.path]
    finally:
        lock.release()
