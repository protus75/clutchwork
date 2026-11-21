# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test brief requisition review
# relates: [clutch/requisition.py]
# owner: clutch/requisition.py
# verified: 595b9e84
# hash: 93315f46fa8bd2e4e1ace7f90d06eafb4cf9689c5010db17a43523dc00c28ccb
import asyncio
import json
from types import SimpleNamespace

from clutch import requisition


def test_single_call_and_context(monkeypatch, tmp_path):
    spec_text = (
        '---\nllm_surface: requisition_review\ntier: high\neffort: high\nversion: "1.0"\n---\n'
        "## Role\nrole\n## Task\ntask\n## Inputs\n"
        "<<clutch-data:begin ticket>>\n{{ticket}}\n<<clutch-data:end ticket>>\n"
        "<<clutch-data:begin context>>\n{{context}}\n<<clutch-data:end context>>\n"
        "<<clutch-data:begin prior_review>>\n{{prior_review}}\n<<clutch-data:end prior_review>>\n"
        "## Output format\njson\n## On-failure\nfail\n"
    )
    (tmp_path / "requisition_review.md").write_text(spec_text)
    (tmp_path / "selected.txt").write_text("unique selected content")
    monkeypatch.setattr(requisition, "review_target", lambda *args: SimpleNamespace(context=("selected.txt",)))
    monkeypatch.setattr(requisition, "_base_render", lambda *args: "base")
    requests = []
    response = {"text": "", "input_tokens": 1, "output_tokens": 2, "provider": "fake", "model": "m", "usd": 0.1}

    async def call(effects, llm, req, redactor, **kwargs):
        requests.append(req)
        return response

    async def race(fn, timeout):
        return await fn()

    monkeypatch.setattr(requisition, "llm_call", call)
    driver = SimpleNamespace(_active=True, spool=SimpleNamespace(write=lambda *args: None), race=race, effects=None, watched_llm=lambda: None, redactor=None)

    def run():
        return asyncio.run(
            requisition.review_ticket(
                driver,
                repo=tmp_path,
                stem="item",
                text="ticket",
                specs_dir=tmp_path,
                coverage_map=None,
                tier="high",
                stem_slot="slot",
                run_seq=1,
                attempt=1,
                call_seq=1,
                expected_budget="surface",
                prior="prior",
            )
        )

    response["text"] = json.dumps({"verdict": "approve", "summary": "fine", "findings": [], "dependents": [{"path": "tests/extra.py", "status": "unaffected", "reason": "still valid"}]})
    result = run()
    assert result.verdict == "approve" and result.calls == 1 and len(requests) == 1
    prompt = requests[0].rendered
    assert prompt.count("unique selected content") == 1
    for block in ("render", "coverage_dependents", "sibling_tickets", "retry_findings"):
        assert f"clutch-data:begin {block}" not in prompt
    response["text"] = "not JSON"
    requests.clear()
    result = run()
    assert result.verdict == "snag" and result.mechanical == "invalid reply" and result.calls == 1 and len(requests) == 1
