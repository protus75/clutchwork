# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the Implement spec Task forbids agent-written clutch:meta headers and meta commands, leaves headers to Check, and says not to report pre-existing meta findings outside the diff
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: d397b992
# hash: 6d1f3e775eb2b7acfc0d983d537b30fbd4c6eb09c82606388668e8b87619f0b9
from pathlib import Path

import pytest

from clutch.specs import load_spec


@pytest.mark.parametrize(
    "clause",
    [
        "Never add, edit, copy or refresh a `clutch:meta` header, and never run `clutch meta refresh`, `clutch meta fill` or `clutch meta check` for the diff.",
        "Check writes headers for every file the diff adds or changes.",
        "Leave pre-existing metadata findings outside the diff alone and do not report them in `second_problems`.",
    ],
)
def test_implement_spec_requires_generated_meta_headers(clause):
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/implement.md").read_text()
    task = " ".join(load_spec(text).body.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0].split())
    # Omitting or reversing this clause would permit the metadata mistake it prevents.
    assert clause in task


def test_step_five_does_not_route_untouched_findings_or_expand_check():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/implement.md").read_text()
    task = " ".join(load_spec(text).body.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0].split())
    step = task.split("5. ", 1)[1].split("6. ", 1)[0].strip()
    # Extra instructions could reinstate filing or claim Check refreshes unrelated files.
    assert step == (
        "Never add, edit, copy or refresh a `clutch:meta` header, and never run `clutch meta refresh`, `clutch meta fill` or `clutch meta check` for the diff. "
        "Check writes headers for every file the diff adds or changes. "
        "Leave pre-existing metadata findings outside the diff alone and do not report them in `second_problems`."
    )
