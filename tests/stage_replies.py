# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared builders for scripted requisition, review and implement LLM replies used by stage tests
# relates: [clutch/requisition.py, clutch/artifacts.py, clutch/stages.py, tests/unit/test_stage_replies.py]
# owner: engine
# verified: 9b76d3e1
# hash: 0a1c194457b884faefc3b3c3dc42af9ff81cf4d731336d77e520b5c056e76eff
import json


def requisition_reply(verdict, findings=None, dependents=None):
    result = {"verdict": verdict, "summary": "reviewed", "findings": findings or []}
    if dependents is not None:
        result["dependents"] = dependents
    return json.dumps(result)


def review_verdict(verdict="approve", findings=None):
    return json.dumps({"verdict": verdict, "summary": "looked", "findings": findings or []})


def implement_reply(outcome: str = "ok", findings: list | None = None) -> str:
    return (
        "```json\n"
        + json.dumps(
            {
                "outcome": outcome,
                "summary": "wrote ok",
                "surprises": "",
                "dead_ends": "none",
                "predicted_vs_actual": "10m predicted, 2m actual",
                "findings": findings or [],
            }
        )
        + "\n```"
    )


def script(*, requisition=None, implement=None, review=None):
    result = []
    for value, builder in ((requisition, requisition_reply), (implement, implement_reply), (review, review_verdict)):
        if value is not None:
            result.append(builder(value) if isinstance(value, str) else value)
    return result
