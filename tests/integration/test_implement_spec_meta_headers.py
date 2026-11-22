# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the Implement spec forbids agent-written clutch:meta headers, leaves headers to Check, and pins spec version 2.26
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 593bc2df
# hash: c22813e73349c9981b6343e4dcecb37d101e0f8c9c789fcac071975481b4b8d9
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


def test_implement_spec_meta_header_version():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/implement.md").read_text()
    # The previous spec version would leave consumers unable to identify the new rule.
    assert load_spec(text).meta.version == "2.26"
