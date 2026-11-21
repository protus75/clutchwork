# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Implement spec requires generated metadata headers
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: a0d5e388
# hash: 6919b9cfeaecb3630dfdb8c47ca2e4193924e95dfa920192b5bdcd6762277f3e
from pathlib import Path

import pytest

from clutch.specs import load_spec


@pytest.mark.parametrize(
    "clause",
    [
        "A new file the diff adds under a configured `meta.paths` root gets its `clutch:meta` header only from `clutch meta fill <path>` or `clutch meta refresh`.",
        "Never type or copy a header: `verified` and `hash` are engine-computed and a hand-typed header fails `parse`.",
        "A file outside `meta.paths` gets no header.",
        "After the last edit and before replying `ok`, run `clutch meta check` and confirm none of the files the diff adds or changes is reported `malformed`, `missing` or `drifted`.",
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
    assert load_spec(text).meta.version == "2.23"
