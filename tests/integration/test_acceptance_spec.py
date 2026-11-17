from pathlib import Path

from clutch.acceptance import AcceptanceReply, GapRow, Promise
from clutch.specs import lint_spec, load_spec, render


def test_acceptance_spec():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/acceptance.md").read_text()
    # A spec with invalid sections or reply instructions must fail lint, not reach a model.
    assert lint_spec(text) == []
    spec = load_spec(text)
    assert spec.meta.model_dump() == dict(llm_surface="acceptance", tier="high", effort="high", version="1.0")
    assert spec.inputs == ("release", "rows", "retry_findings")
    rendered = render(spec, {"release": '{"release":"1.0.0"}', "rows": '[{"number":71}]', "retry_findings": '["correct source"]'})
    assert all(value in rendered for value in ('{"release":"1.0.0"}', '[{"number":71}]', '["correct source"]'))
    output = text.split("## Output format\n")[1].split("## On-failure\n")[0]
    for field in set(AcceptanceReply.model_fields) | set(Promise.model_fields) | set(GapRow.model_fields) | {"met", "partial", "unmet", "deferred"}:
        assert f"`{field}`" in output
