# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the Implement spec requires finishing mutation checks before replying, forbids replying incomplete over them, and pins version 2.26
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 593bc2df
# hash: 3fca59eeb943790b7bfb58c523a07ba82ccdf12511afa1399851ab450124778c
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
    assert load_spec(text).meta.version == "2.26"
