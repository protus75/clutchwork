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
