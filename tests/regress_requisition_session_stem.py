"""Reproduce a missing ticket stem on requisition review requests."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone regression script that runs a fake-LLM driver stage with a requisition review and checks that the review request carries the reviewed ticket stem; it exits 0 on pass, 1 on defect and 2 on error.
# relates: [clutch/config.py, clutch/driver.py, clutch/gates.py, clutch/journal.py, clutch/llm.py, clutch/requisition.py]
# owner: engine
# verified: fb61b143
# hash: 3f19a9078d8c34c9a6642f81bdd711793a7987fc0676eab772eb5a142f95399e

import asyncio
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from clutch.config import load_config
from clutch.driver import Driver, LlmStage
from clutch.gates import GateReport
from clutch.journal import Journal
from clutch.llm import FakeLLM
from clutch.requisition import FIRST_REVIEW, review_ticket

TICKET = """---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
none

## Context
- context.txt

## Goal / Why
Create one thing.

## Boundary contract
none
- reason: unchanged behavior

## Scope in / Scope out
In: thing. Out: the rest.

## Scope fence
- thing.py

## Acceptance criteria
1. `thing.py` exists, checked by `test -f thing.py`.

## Verification
```
test -f thing.py
```

## Definition of rejected
Needs an outside file.

## Time budget
- expected: 10m
- stuck: 20m
"""
CONFIG = """schema_version: 1
state_dir: .state
providers:
  - name: fake
    kind: cli
    package: test-cli
    auth: FAKE_KEY
    models_by_tier: {low: m, medium: m, high: m, max: m}
    limits: {concurrency: 1, est_cost_per_call_usd: 0.5}
routing:
  - {tier: high, surface: review, candidates: [{provider: fake}]}
review: {}
merge: {}
engine_plane_safety_inventory: [context.txt]
"""


async def never(seconds):
    await asyncio.Event().wait()


class Reply(BaseModel):
    value: str


def main() -> None:
    scratch = Path(__file__).resolve().parents[1] / ".clutch/scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as directory:
        repo = Path(directory)
        (repo / "context.txt").write_text("context")
        (repo / "config.yaml").write_text(CONFIG)
        llm = FakeLLM([json.dumps({"value": "proposal"}), json.dumps({"verdict": "approve", "summary": "reviewed", "findings": []})])
        driver = Driver.from_config(
            load_config(None, cwd=repo),
            journal=Journal((load_config(None, cwd=repo)).state_dir, lambda: datetime(2026, 10, 6, tzinfo=UTC)),
            llm=llm,
            env={"FAKE_KEY": "secret"},
            clock=lambda: datetime(2026, 10, 6, tzinfo=UTC),
            sleep=never,
        )

        async def review(artifact, call_seq):
            verdict = await review_ticket(
                driver,
                repo=repo,
                stem="candidate",
                text=TICKET,
                specs_dir=Path(__file__).resolve().parents[1] / "clutch/specs",
                coverage_map=None,
                tier="high",
                stem_slot="owner",
                run_seq=4,
                attempt=2,
                call_seq=call_seq,
                expected_budget="surface",
                prior=FIRST_REVIEW,
            )
            return GateReport(code="requisition_review", verdict="pass" if verdict.verdict == "approve" else "fail", findings=verdict.findings)

        asyncio.run(
            driver.run(
                LlmStage(surface="author", emits=Reply, gates=[], render=lambda consumed, findings: "proposal", review=review),
                None,
                ticket=None,
                run_seq=4,
                attempt=2,
                workspace=repo,
                tier="high",
                effort="high",
                stuck_budget=600,
                expected_budget="surface",
                scope_fence=(),
            )
        )
        request = next((request for request in llm.requests if request.surface == "requisition_review"), None)
        result = "error" if request is None else "pass" if request.ticket == "candidate" else "defect"
        print(json.dumps({"regression_result": result}))
        raise SystemExit({"pass": 0, "defect": 1, "error": 2}[result])


if __name__ == "__main__":
    main()
