# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test implement spec mutation check
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 11318b79
# hash: 45437fc206c90703b485924530600fdeb657dd360c25e90e89155216eee45c0b
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
    assert load_spec(text).meta.version == "2.22"
