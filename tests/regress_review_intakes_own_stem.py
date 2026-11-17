"""Reproduce review intaking another pending ticket."""

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
        env = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com", "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}

        def git(*args):
            return subprocess.run(["git", "-C", str(repo), *args], env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout

        git("init", "-b", "main")
        git("add", ".")
        git("commit", "-m", "initial")
        for stem in ("alpha", "beta"):
            path = repo / "tickets" / stem / "ticket.md"
            path.parent.mkdir(parents=True)
            path.write_text(TICKET.format(depends="none").replace("---\npriority:", "---\nstate: draft\npriority:", 1))
        llm = FakeLLM([json.dumps({"verdict": "approve", "summary": "reviewed", "findings": []})])
        with patch("clutch.__main__.ProviderLLM", return_value=llm), contextlib.redirect_stdout(io.StringIO()):
            result = clutch_main(["ticket", "review", "alpha"], cwd=repo, env=env)
        subjects = git("log", "--format=%s").splitlines()
        if "clutch(beta): ticket" in subjects:
            outcome = "defect"
        elif result == 0 and "clutch(alpha): ticket" in subjects and "state: draft" in (repo / "tickets/beta/ticket.md").read_text():
            outcome = "pass"
        else:
            outcome = "error"
        print(json.dumps({"regression_result": outcome}))
        raise SystemExit(0 if outcome == "pass" else 1)


if __name__ == "__main__":
    main()
