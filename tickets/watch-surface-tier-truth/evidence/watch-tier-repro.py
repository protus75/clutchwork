"""Reproduce: watch's 'asked for tier/effort' vs the tier/effort the engine passes, per ticket surface."""
import json, os, shutil, sys
from pathlib import Path
from types import SimpleNamespace

repo = Path(sys.argv[1]); sandbox = Path(sys.argv[2])
sys.path.insert(0, str(repo))
import clutch.observe as watch
from clutch.caps import capability
from tests.integration.test_config import VALID

shutil.rmtree(sandbox, ignore_errors=True)
(sandbox / "tickets/alpha").mkdir(parents=True)
(sandbox / "config.yaml").write_text(VALID)
(sandbox / "tickets/alpha/ticket.md").write_text("---\nstate: confirmed\npriority: P1\n---\n## Depends on\nnone\n")
state = sandbox / "state"; (state / "journal").mkdir(parents=True)
(state / "clutch.lock").write_text(json.dumps({"pid": os.getpid(), "started_at": "2026-11-15T10:00:00+00:00"}))
(state / "journal/000001.jsonl").write_text(json.dumps({"type": "state_transition", "ticket": "alpha", "body": {"to": "running"}, "ts": "2026-11-15T10:01:00+00:00"}) + "\n")
watch.processes = lambda ctx: []
watch.committed_ticket_shas = lambda ctx: {}
ctx = watch.Context(sandbox, state, sandbox / "config.yaml", None, None, None)
ticket = SimpleNamespace(stem="alpha", frontmatter=SimpleNamespace(agent_tier="medium", agent_effort="medium"))
engine_tier, engine_effort = capability(ticket, [])
spec_effort = {s: watch.frontmatter(repo / "clutch/specs" / f"{s}.md").get("effort") for s in ("requisition_review",)}
engine = {
    "requisition_review": f"{engine_tier}/{spec_effort['requisition_review']}",  # runner.drive: tier=caps.capability; requisition.review_ticket: effort=spec.meta.effort
    "implement": f"{engine_tier}/{engine_effort}",  # stages.implement: ticket.frontmatter.agent_tier/agent_effort
    "review": f"{engine_tier}/{engine_effort}",  # stages.review: ticket.frontmatter.agent_tier/agent_effort
    "diagnose": f"{engine_tier}/{engine_effort}",  # stages.diagnose: ticket.frontmatter.agent_tier/agent_effort
    "rework": f"{engine_tier}/{engine_effort}",  # daemon.apply_rework: runner.capability(original)
}
print("ticket alpha: agent_tier/agent_effort = medium/medium (Frontmatter defaults), no escalation rung")
print()
for surface, truth in engine.items():
    (state / "engine.log").write_text(json.dumps({"ts": "2026-11-15T10:02:00+00:00", "event": "stage_start", "stem": "alpha", "attempt": 1, "surface": surface}) + "\n")
    now = [l for l in watch.text_snapshot(ctx).splitlines() if l.startswith("Now:") or "asked for" in l]
    shown = now[1].split("asked for tier/effort ", 1)[1]
    print(f"surface={surface:<19} watch: {' | '.join(s.strip() for s in now)}")
    print(f"{'':27}engine passes tier/effort {truth}   -> {'MATCH' if shown == truth else 'MISMATCH'}")
