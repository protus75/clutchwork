# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test artifacts refused
# relates: [clutch/artifacts.py]
# owner: clutch/artifacts.py
# verified: 0a308920
# hash: 33c4e32f37dd81270fd54c12b73020a4a77aa9843aff2e2746a5c412c3e09c6f
from clutch.artifacts import Artifact, Cost, Finding, refused


def test_refused_preserves_findings_cost_and_optional_artifact():
    finding = Finding(code="scope_fence", message="outside fence", paved_road="extend fence")
    artifact = Artifact(produced_by_spec_version=1, produced_at_sha="abc")
    result = refused([finding], Cost(seconds=2))
    assert result.outcome == "gate_failed"
    assert result.artifact is None
    assert result.findings == [finding]
    assert result.cost.seconds == 2
    assert refused([finding], Cost(seconds=2), artifact=artifact).artifact is artifact
