# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test asserting that requisition.review_ticket sends its requisition_review LLM request tagged with the reviewed ticket stem.
# relates: [clutch/llm.py, clutch/requisition.py]
# owner: engine
# verified: fb61b143
# hash: b8cab74ff5fc461214cb3292c43ed7f5d189cb0b1181a9be4ed67b303f6c9b7c
import asyncio
import json
from dataclasses import asdict
from types import SimpleNamespace

from clutch import requisition
from clutch.llm import FakeLLM


def test_requisition_review_request_has_reviewed_stem(monkeypatch, tmp_path):
    (tmp_path / "requisition_review.md").write_text(
        '---\nllm_surface: requisition_review\ntier: high\neffort: high\nversion: "1.0"\n---\n'
        "## Role\nrole\n## Task\ntask\n## Inputs\n"
        "<<clutch-data:begin ticket>>\n{{ticket}}\n<<clutch-data:end ticket>>\n"
        "<<clutch-data:begin context>>\n{{context}}\n<<clutch-data:end context>>\n"
        "<<clutch-data:begin prior_review>>\n{{prior_review}}\n<<clutch-data:end prior_review>>\n"
        "## Output format\njson\n## On-failure\nfail\n"
    )
    (tmp_path / "context.txt").write_text("context")
    monkeypatch.setattr(requisition, "review_target", lambda *args: SimpleNamespace(context=("context.txt",)))
    monkeypatch.setattr(requisition, "_base_render", lambda *args: "base")
    llm = FakeLLM([json.dumps({"verdict": "approve", "summary": "reviewed", "findings": []})])

    async def call(effects, llm, req, redactor, **kwargs):
        return asdict(await llm.call(req))

    async def race(fn, timeout):
        return await fn()

    monkeypatch.setattr(requisition, "llm_call", call)
    driver = SimpleNamespace(_active=True, spool=SimpleNamespace(write=lambda *args: None), race=race, effects=None, watched_llm=lambda: llm, redactor=None)
    asyncio.run(
        requisition.review_ticket(
            driver,
            repo=tmp_path,
            stem="abc",
            text="ticket",
            specs_dir=tmp_path,
            coverage_map=None,
            tier="high",
            stem_slot="owner",
            run_seq=1,
            attempt=1,
            call_seq=1,
            expected_budget="surface",
            prior=requisition.FIRST_REVIEW,
        )
    )
    request = next(request for request in llm.requests if request.surface == "requisition_review")
    assert request.ticket == "abc"
