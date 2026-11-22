# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that the shared stage reply builders produce schema-valid replies and stay independent of integration tests
# relates: [clutch/artifacts.py, clutch/requisition.py, clutch/stages.py, tests/stage_replies.py]
# owner: engine
# verified: 9b76d3e1
# hash: f904f8876a844f8e0e260301d2d87ffd6672b0a41ad97d53b6004ad656ea0da4
import inspect
import json

from clutch.artifacts import ReviewVerdict
from clutch.requisition import RequisitionReply
from clutch.stages import ImplementReply
from tests import stage_replies
from tests.stage_replies import implement_reply, requisition_reply, review_verdict, script

FINDING = {"code": "logic", "message": "wrong", "paved_road": "fix it"}
DEPENDENT = {"path": "tests/example.py", "status": "fenced", "reason": "affected"}


def test_requisition_reply():
    assert requisition_reply("approve") == json.dumps({"verdict": "approve", "summary": "reviewed", "findings": []})
    assert json.loads(requisition_reply("approve", None, []))["dependents"] == []
    parsed = RequisitionReply.model_validate_json(requisition_reply("snag", [FINDING], [DEPENDENT]))
    assert parsed.findings[0].message == "wrong"
    assert parsed.dependents[0].path == "tests/example.py"
    assert json.loads(requisition_reply("wrong"))["verdict"] == "wrong"


def test_review_and_implement_shapes():
    review = review_verdict("snag", [FINDING])
    assert ReviewVerdict.model_validate_json(review).findings[0].code == "logic"
    report = implement_reply()
    assert report.startswith("```json\n") and report.endswith("\n```")
    assert ImplementReply.model_validate_json(report[len("```json\n") : -len("\n```")]).summary == "wrote ok"


def test_script_order_and_passthrough():
    def callback(request):
        return request

    assert script(requisition="approve", implement="ok", review="approve") == [requisition_reply("approve"), implement_reply("ok"), review_verdict("approve")]
    assert script(review="snag") == [review_verdict("snag")]
    assert script(implement=callback)[0] is callback


def test_shared_module_has_no_integration_dependency():
    assert "tests.integration" not in inspect.getsource(stage_replies)
