"""Guard shared stage replies and config fixtures across the test tree."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Fails when a test module outside tests/stage_replies.py or tests/config_fixture.py defines its own stage reply helper or inline test config text, and flags any exemption that is stale or has no reason.
# relates: [tests/stage_replies.py, tests/config_fixture.py, tests/unit/test_config_fixture.py]
# owner: engine
# verified: c589fb97
# hash: 7ed63beea98ae8e38f6436a7e4440d077e1ac2371aeabd88d8bd0ea289565693

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPLY_EXEMPT = {
    "tests/integration/test_serve_verdict_orphan_sweep.py": "Async callback controls the verdict sweep, not a model reply.",
    "tests/unit/test_lock_holder.py": "Async callback simulates a held lock.",
    "tests/unit/test_requisition_prior_review.py": "Builds a journal event rather than a model reply.",
    "tests/unit/test_stale_running.py": "Async callback records the verdict command.",
}
CONFIG_EXEMPT = {
    "tests/integration/test_config.py": "Exercises config parsing and validation.",
    "tests/integration/test_diagnose_eval.py": "Exercises diagnosis evaluation configuration.",
    "tests/integration/test_driver.py": "Exercises driver configuration.",
    "tests/integration/test_echo_stage.py": "Exercises echo stage configuration.",
    "tests/integration/test_eval_harness.py": "Exercises evaluation harness configuration.",
    "tests/integration/test_gates.py": "Exercises gate configuration.",
    "tests/integration/test_ladder.py": "Exercises ladder configuration.",
    "tests/integration/test_llm_effect.py": "Exercises LLM effect configuration.",
    "tests/integration/test_policy.py": "Exercises policy configuration.",
    "tests/integration/test_requisition.py": "Exercises requisition configuration.",
    "tests/unit/test_config_fixture.py": "Pins the original configs for builder compatibility.",
    "tests/unit/test_context_suggest_verb.py": "Exercises context suggestion configuration.",
    "tests/unit/test_driver_from_config_journal.py": "Exercises driver configuration and journal behavior.",
    "tests/unit/test_index_config.py": "Exercises index configuration.",
    "tests/unit/test_route_kinds_filter.py": "Exercises route kind filtering.",
}
REPLY_NAMES = {"requisition_reply", "review_verdict", "implement_reply", "verdict"}


def scan(files, reply_exempt, config_exempt):
    """Return findings for new copies, stale exemptions and missing reasons."""
    matches = [set(), set()]
    findings = []
    for path, source in files.items():
        tree = ast.parse(source, filename=path)
        if path != "tests/stage_replies.py" and any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in REPLY_NAMES for node in ast.walk(tree)):
            matches[0].add(path)
        if path != "tests/config_fixture.py" and any(
            isinstance(node, ast.Constant) and isinstance(node.value, str) and "schema_version:" in node.value and "routing:" in node.value for node in ast.walk(tree)
        ):
            matches[1].add(path)
    for found, exemptions, road in (
        (matches[0], reply_exempt, "import it from tests/stage_replies.py"),
        (matches[1], config_exempt, "build it with tests/config_fixture.py::build_config"),
    ):
        for path in sorted(found - exemptions.keys()):
            findings.append(f"{path}: {road}")
        for path, reason in sorted(exemptions.items()):
            if not reason.strip():
                findings.append(f"{path}: exemption needs a reason")
            if path not in found:
                findings.append(f"{path}: stale exemption")
    return findings


def test_shared_fakes_guard():
    files = {path.relative_to(ROOT).as_posix(): path.read_text() for path in (ROOT / "tests").rglob("*.py") if not path.name.startswith("regress_")}
    assert scan(files, REPLY_EXEMPT, CONFIG_EXEMPT) == []


def test_scan_reports_new_copies_and_excludes_owners():
    reply = "def requisition_reply():\n    pass\n"
    config = repr("schema_version: 1\n" + "routing: []\n")
    files = {
        "tests/new_reply.py": reply,
        "tests/new_config.py": config,
        "tests/stage_replies.py": reply,
        "tests/config_fixture.py": config,
    }
    assert scan(files, {}, {}) == [
        "tests/new_reply.py: import it from tests/stage_replies.py",
        "tests/new_config.py: build it with tests/config_fixture.py::build_config",
    ]


def test_scan_reports_stale_and_unexplained_exemptions():
    files = {"tests/old.py": "pass\n", "tests/config_old.py": "pass\n"}
    assert scan(files, {"tests/old.py": " "}, {"tests/config_old.py": "reason"}) == [
        "tests/old.py: exemption needs a reason",
        "tests/old.py: stale exemption",
        "tests/config_old.py: stale exemption",
    ]
