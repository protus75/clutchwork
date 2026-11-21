# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose:
# relates: []
# owner: engine
# verified: ceaeffc2
# hash: 01e299afc77fa9b941310666e4b018053afee1aac9d3f9aa8b8c3db828b864bf
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "clause",
    [
        "the run record or checks show that an engine step wrote the failing lines onto the candidate after Implement",
        "the cause is engine code outside the fence",
        "Name the engine file and the defect in the lessons.",
        "Never choose `retry` with a lesson asking the implementer to pre-empt the engine output.",
        "When the implementer's diff produced the failing content, keep the normal verdicts: `retry`, `escalate`, `split` or `reject`.",
    ],
)
def test_engine_written_failure_verdict(clause):
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/diagnose.md").read_text()
    verdict = text.split("- `abandon-human`:", 1)[1].split("\n\n", 1)[0]
    # Removing each clause permits an unevidenced abandon or an incorrect lesson or verdict.
    assert clause in verdict
