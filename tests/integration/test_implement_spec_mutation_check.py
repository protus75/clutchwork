# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the Implement spec requires finishing mutation checks before replying and forbids replying incomplete over unfinished mutation checks
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: c62231b6
# hash: 3f35dd7ec52fc23746af89d44c3f590e75ec6a9c223ef75665c203010d906ce1
from pathlib import Path


def test_implement_spec_finishes_mutation_checks_before_replying():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/implement.md").read_text()
    # The prior version omitted each instruction and retained the old version.
    assert (
        "Finish the check for every assertion before replying, and if time is short, finish it and restore the code "
        "rather than stopping partway; unfinished mutation checks are never a reason to reply `incomplete`." in text
    )
    assert "Never use `incomplete` because mutation checks remain while the Verification commands pass." in text
