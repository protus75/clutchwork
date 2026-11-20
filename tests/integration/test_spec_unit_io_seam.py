# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test spec unit io seam
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 96e46658
# hash: 65697932836405772963272e9da3ddefc0277bd418a933733f435cc11aadb752
from pathlib import Path

from clutch.specs import load_spec

SPECS = Path(__file__).resolve().parents[2] / "clutch" / "specs"


def test_requisition_review_spec_snags_unit_io_with_seam_road():
    text = (SPECS / "requisition_review.md").read_text()
    task = " ".join(load_spec(text).body.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0].split())
    # Missing any phrase overlooks an I/O case, coverage requirement, or exemption.
    for phrase in (
        "makes a `tests/unit/` test write disk outside `tmp_path`, start a process, or open a network connection, "
        "raise a `snag` finding: place that test under `tests/integration/` and fence that file",
        "hits a test that must run new lines in a file with a floor above 0 under `[coverage.files]`",
        "its paved road also names an in-fence seam, such as an injected reader or a parameter carrying the bytes, through which a fenced `tests/unit` test runs those lines with a fake",
        "moves only the real disk, process, or network checks to `tests/integration/`",
        "A test using only in-memory buffers or fakes is not a hit.",
        "No seam is required for an I/O site where Scope in adds no line.",
    ):
        assert phrase in task


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
