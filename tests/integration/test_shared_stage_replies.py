# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Guards that migrated integration test files use the shared stage reply builders instead of local copies
# relates: [tests/integration/test_stages.py, tests/stage_replies.py]
# owner: engine
# verified: 9b76d3e1
# hash: 6228c12afa870df7ac93c48b4bd425c208d9a534a4518789f2895643d69244d5
import ast
from pathlib import Path

from tests.integration.test_stages import implement_reply, verdict
from tests.stage_replies import implement_reply as shared_implement_reply
from tests.stage_replies import review_verdict

ROOT = Path(__file__).resolve().parents[1]
MIGRATED = ("test_stages.py", "test_requisition.py", "test_requisition_gate.py", "test_author.py", "test_triage.py", "test_review_command.py")


def test_migrated_files_use_shared_builders():
    for name in MIGRATED:
        source = (ROOT / "integration" / name).read_text()
        for text in ("def verdict(", "def implement_reply(", "def requisition_reply(", '"summary": "reviewed"', '"summary": "looked"', '"predicted_vs_actual"'):
            assert text not in source, (name, text)
        tree = ast.parse(source)
        wrappers = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "reply"]
        if name in ("test_requisition.py", "test_requisition_gate.py"):
            assert len(wrappers) == 1
            assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "requisition_reply" for node in ast.walk(wrappers[0]))
        if name == "test_review_command.py":
            assert not wrappers


def test_shared_source_and_compatibility_exports():
    source = (ROOT / "stage_replies.py").read_text()
    assert '"summary": "looked"' in source
    assert '"predicted_vs_actual"' in source
    assert verdict is review_verdict
    assert implement_reply is shared_implement_reply
