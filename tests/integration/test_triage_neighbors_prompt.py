# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Triage spec neighbors block renders quoted
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: dd604324
# hash: 1de8ac315d20e5948ac5a50725ed06845ca46a12a2a3f7d4c4d966270692a85c
from pathlib import Path

from clutch.specs import DATA_DELIM, data_open, lint_spec, load_spec, render, validate_data_blocks


def test_neighbors_payload_is_quoted():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/triage.md").read_text()
    # Wrong: a malformed spec or a missing declared input.
    assert lint_spec(text) == []
    spec = load_spec(text)
    assert "neighbors" in spec.inputs
    payload = DATA_DELIM + "end neighbors>>"
    prompt = render(spec, {key: payload if key == "neighbors" else "evidence" for key in spec.inputs})
    # Wrong: allowing the payload to close the block or introducing an extra block.
    assert "[clutch-data:end neighbors>>" in prompt
    assert prompt.count(data_open("neighbors")) == 1
    assert validate_data_blocks(prompt) == []
