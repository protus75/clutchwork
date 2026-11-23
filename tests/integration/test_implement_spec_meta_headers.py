# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the Implement spec Task forbids agent-written clutch:meta headers and meta commands, leaves headers to Check, and routes untouched-file meta findings to second_problems
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: c62231b6
# hash: 1229ea08f5df575aad87ff32fd003ca126a3054bf77d6d44c126cd7e9fd2a3cb
from pathlib import Path

import pytest

from clutch.specs import load_spec


@pytest.mark.parametrize(
    "clause",
    [
        "Never add, edit, copy or refresh a `clutch:meta` header, and never run `clutch meta refresh`, `clutch meta fill` or `clutch meta check` for the diff.",
        "Check writes headers for every file the diff adds or changes.",
        "A meta finding on a file the diff does not touch goes to `second_problems`; never fix it in this diff.",
    ],
)
def test_implement_spec_requires_generated_meta_headers(clause):
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/implement.md").read_text()
    task = " ".join(load_spec(text).body.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0].split())
    # Omitting or reversing this clause would permit the metadata mistake it prevents.
    assert clause in task
