# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the Implement spec requires finishing mutation checks before replying and never replying incomplete over them
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 9be395f4
# hash: 5b18c3c3e6dbb1f05234ea7adf7b8437f0a4ff3a48566f9597835368a8b4f5f4
from pathlib import Path

from clutch.specs import load_spec


def test_implement_spec_finishes_mutation_checks_before_replying():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/implement.md").read_text()
    # The prior version omitted each instruction and retained the old version.
    assert (
        "Finish the check for every assertion before replying, and if time is short, finish it and restore the code "
        "rather than stopping partway; unfinished mutation checks are never a reason to reply `incomplete`." in text
    )
    assert "Never use `incomplete` because mutation checks remain while the Verification commands pass." in text
    assert load_spec(text).meta.version == "2.25"
