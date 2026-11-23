# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks every prompt spec's Role explains quoted data delimiters, pins non-implement spec versions, and renders delimiter payloads quoted
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 800fa1a3
# hash: 64496c55d94cecf2995edff930d0ab3fd2f7430a2b8ed76319439bb60b167fc6
from pathlib import Path

import pytest

from clutch.specs import DATA_DELIM, data_close, data_open, lint_spec, load_spec, render


@pytest.mark.parametrize(
    ("name", "version"),
    [
        ("acceptance", "1.0"),
        ("author", "1.11"),
        ("diagnose", "1.11"),
        ("implement", None),
        ("requisition_review", "3.29"),
        ("retro", "1.7"),
        ("review", "1.9"),
        ("rework", "1.3"),
        ("triage", "1.1"),
    ],
)
def test_role_explains_quoted_delimiters(name, version):
    text = (Path(__file__).resolve().parents[2] / "clutch" / "specs" / f"{name}.md").read_text()
    assert lint_spec(text) == []
    spec = load_spec(text)
    if version is not None:
        assert spec.meta.version == version
    role = spec.body.split("## Role\n", 1)[1].split("## Task\n", 1)[0]
    note = (
        "In any data block, `[clutch-data:` is the renderer's quoting of the real delimiter, "
        "which is two less-than signs followed by `clutch-data:` in the file on disk; a ticket or text "
        "naming that delimiter is correct as written and never an error or a false premise."
    )
    assert note in role
    payload = DATA_DELIM + "begin x>>"
    rendered = render(spec, {key: payload for key in spec.inputs})
    assert note in rendered.split("## Role\n", 1)[1].split("## Task\n", 1)[0]
    for key in spec.inputs:
        block = rendered.split(data_open(key) + "\n", 1)[1].split("\n" + data_close(key), 1)[0]
        assert block == "[clutch-data:begin x>>"
        assert payload not in block
