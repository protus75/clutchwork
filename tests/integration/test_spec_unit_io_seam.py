# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test spec unit io seam
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 595b9e84
# hash: 982125d968857f0c10cc417a92472897b75858d1a994a35e879a694e132d735d
from pathlib import Path

from clutch.specs import load_spec

SPECS = Path(__file__).resolve().parents[2] / "clutch" / "specs"


def test_diagnose_spec_keeps_floored_lines_unit_reachable():
    text = (SPECS / "diagnose.md").read_text()
    task = " ".join(load_spec(text).body.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0].split())
    # Missing any phrase permits a lesson to lose coverage or omit the seam's location.
    for phrase in (
        "When a lesson moves a test out of `tests/unit/` and that test must run lines the ticket adds to a file with a floor above 0 under `[coverage.files]` in `test-gate.toml`",
        "the lesson keeps those lines reachable from `tests/unit/`: it names that file and the I/O call there that needs "
        "an in-fence seam, such as an injected reader or a parameter carrying the bytes",
        "it moves only the real disk, process, or network checks to `tests/integration/`",
        "Never tell the author to drop unit coverage of those lines.",
    ):
        assert phrase in task
