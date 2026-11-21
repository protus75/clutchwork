# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Metadata drift gate severity and bypass
# relates: [clutch/artifacts.py, clutch/gates.py, clutch/stages.py, clutch/tickets.py]
# owner: engine
# verified: 75d75946
# hash: 0289b3b781c7a279fccdef403e69a2de922112a5ef74bc19d49c5808569b79d5
from clutch.artifacts import Finding
from clutch.gates import DEFAULT_GATE_SEVERITY, ENGINE_GATE_CODES, merge_severity, run_gates
from clutch.stages import Evidence, MetaDriftGate
from clutch.tickets import Frontmatter


def test_gate_severity_and_bypass(tmp_path):
    assert DEFAULT_GATE_SEVERITY["meta_drift"] == "soft"
    assert len(ENGINE_GATE_CODES) == 12
    assert all(DEFAULT_GATE_SEVERITY[code] == "hard" for code in ENGINE_GATE_CODES - {"meta_drift"})
    assert merge_severity(None)["meta_drift"] == "soft"
    front = Frontmatter(state="confirmed", source="human", priority="P2", kind="feature", gate_bypass=[{"code": "meta_drift", "reason": "reviewed"}])
    assert front.gate_bypass[0].code == "meta_drift"
    finding = Finding(code="meta_drift", path="docs/a.md", message="docs/a.md: malformed", paved_road="fix the block")
    evidence = Evidence(stem="work", head_sha="abc", claimed="ok", scope_fence=[], changed_files=[], inserted_lines=0, verification=[], run_record=None, meta_findings=[finding])
    soft = run_gates([MetaDriftGate()], evidence, tmp_path)
    assert soft.passed and len(soft.soft_failures) == 1 and soft.soft_failures[0].findings == [finding]
    hard = run_gates([MetaDriftGate()], evidence, tmp_path, severity={"meta_drift": "hard"})
    assert not hard.passed and len(hard.hard_failures) == 1 and hard.hard_failures[0].code == "meta_drift"
    assert run_gates([MetaDriftGate()], evidence.model_copy(update={"meta_findings": []}), tmp_path).reports[0].verdict == "pass"
