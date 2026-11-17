"""Reproduce a review that forgets the preceding recorded finding."""

import contextlib
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from clutch.__main__ import main as clutch_main
from clutch.config import load_config
from clutch.hostfiles import render
from clutch.llm import FakeLLM
from clutch.providers import routed_conduct_paths

CONFIG = """schema_version: 1
state_dir: .clutch/state
providers:
  - name: claude
    kind: cli
    package: test-cli
    models_by_tier: {low: m, medium: m, high: m, max: m}
    limits: {concurrency: 1}
routing:
  - {tier: medium, surface: implement, candidates: [{provider: claude}]}
review: {}
merge: {}
engine_plane_safety_inventory: [config.yaml]
"""
PLAN = """# Plan

## 11. Failure spine

Spine.
"""
TICKET = """---
priority: P2
kind: feature
---

## Depends on
{depends}

## Context
- clutch/thing.py

## Goal / Why
`thing()` returns ok.

## Scope in / Scope out
In: thing. Out: the rest.

## Scope fence
- clutch/thing.py

## Acceptance criteria
1. `uv run pytest` exits 0.

## Verification
```
uv run pytest
```

## Definition of rejected
Needs a new dependency.

## Time budget
- expected: 10m
- stuck: 20m
"""


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repo = Path(directory)
        (repo / "clutch").mkdir()
        (repo / "clutch/thing.py").write_text("")
        (repo / "config.yaml").write_text(CONFIG)
        (repo / "CLUTCH_PLAN.md").write_text(PLAN)
        (repo / ".gitignore").write_text(".clutch/\n")
        for path in routed_conduct_paths(load_config(None, cwd=repo), repo):
            path.write_bytes(render(path.read_bytes() if path.exists() else b""))
        path = repo / "tickets/candidate/ticket.md"
        path.parent.mkdir(parents=True)
        path.write_text(TICKET.format(depends="none").replace("---\npriority: P2", "---\nstate: confirmed\nsource: human\npriority: P2", 1))
        env = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com", "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}

        def git(*args):
            subprocess.run(["git", "-C", str(repo), *args], env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        git("init", "-b", "main")
        git("add", ".")
        git("commit", "-m", "initial")
        finding = {"code": "missing", "message": "missing caller", "paved_road": "add caller"}
        llm = FakeLLM([json.dumps({"verdict": "snag", "summary": "reviewed", "findings": [finding]}), json.dumps({"verdict": "approve", "summary": "reviewed", "findings": []})])
        with patch("clutch.__main__.ProviderLLM", return_value=llm):
            with contextlib.redirect_stdout(io.StringIO()):
                first = clutch_main(["review", "candidate"], cwd=repo, env=env)
            path.write_text(path.read_text().replace("## Goal / Why", "## Goal / Why\nEdited."))
            git("add", "tickets/candidate/ticket.md")
            git("commit", "-m", "edit")
            with contextlib.redirect_stdout(io.StringIO()):
                second = clutch_main(["review", "candidate"], cwd=repo, env=env)
        block = llm.requests[1].rendered.split("<<clutch-data:begin prior_review>>\n", 1)[1].split("\n<<clutch-data:end prior_review>>", 1)[0]
        passed = first == 1 and second == 0 and "missing caller" in block
        print(json.dumps({"regression_result": "pass" if passed else "defect"}))
        raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
