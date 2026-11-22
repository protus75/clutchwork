# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the authoring guide, Implement/Review/Retro specs and how-clutch-works doc state the unit-test tmp_path-only disk I/O rule and drop the old bans
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 593bc2df
# hash: b25bd16f2417a8b8cf5d04ba0ce153711e78c73afc14e4199030ee82e3219203
from pathlib import Path

from clutch.specs import load_spec

ROOT = Path(__file__).resolve().parents[2]


def test_authoring_guide_states_unit_test_io_rule():
    text = (ROOT / "clutch/docs/host-authoring.md").read_text()
    lines = text.splitlines()
    # Missing or misplaced headings leave authors without the rule in its intended section.
    assert lines.index("## Keeping tickets apart") < lines.index("## Unit and integration tests") < lines.index("## Path matching")
    guide = " ".join(text.split())
    # Each missing phrase loses an I/O restriction, placement exception, or coverage road.
    for phrase in (
        "A test under `tests/unit/` reads and writes disk only under `tmp_path`; it never reads or writes a repo file, starts a process, or opens a network connection.",
        "`clutch.testguard` blocks processes and network connections but not disk",
        "Place a test that reads a repo file under `tests/integration/` and fence that file.",
        "An integration test never writes to disk, starts a process, runs git, or opens a network connection or an on-disk database; it drives the code through in-memory fakes.",
        "Only a test whose subject is a real I/O function touches real disk or processes, and its file is in the host's explicit allowlist (in clutch's own repo, `REAL_IO_TESTS` in `tests/integration/conftest.py`).",
        "Test temporary files never go to `/tmp`.",
        "A test using only `tmp_path`, in-memory buffers, or fakes stays under `tests/unit/`, as does a test that reaches a repo file only through an injected seam or fake.",
        "Updating a pinned value in an existing unit test that already reads a repo file does not move that test.",
        "When Scope in adds lines to a file with a floor above 0 under `[coverage.files]` in `test-gate.toml`, a fenced `tests/unit/` test runs those lines.",
        "When running those lines needs a repo file, a process, or the network, Scope in names an in-fence seam, such as an injected reader or a parameter carrying the bytes, "
        "through which a fenced `tests/unit` test runs those lines with a fake, and covers the real disk, process, or network site only in an allowlisted real-I/O test.",
        "No seam is required for an I/O site where Scope in adds no line.",
    ):
        assert phrase in guide
    # The old placement rule would still send process and network tests to integration.
    assert "Place a test that needs a repo file, a process, or the network" not in guide
    for name, old in (("retro", "or move it to integration"), ("implement", "a process boundary or real files")):
        task = load_spec((ROOT / f"clutch/specs/{name}.md").read_text()).body.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0]
        assert old not in " ".join(task.split())


def test_rule_copies_allow_only_tmp_path_disk():
    # Old bans must disappear as well as the new restrictions appearing in each task.
    for name, required, forbidden in (
        ("implement", "It reads and writes disk only under `tmp_path`; it never reads or writes a repo file, starts a process, or opens a network connection", "It never reads or writes disk"),
        ("review", "a unit test that reads or writes disk outside `tmp_path`, opens a network connection", "a unit test that reads or writes disk, opens"),
        ("retro", "`unit-io`: a unit test touches disk outside `tmp_path`, network or a real process", "a unit test touches disk, network"),
    ):
        text = (ROOT / f"clutch/specs/{name}.md").read_text()
        task = " ".join(load_spec(text).body.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0].split())
        assert required in task
        assert forbidden not in task
    docs = " ".join((ROOT / "docs/how-clutch-works.md").read_text().split())
    # The documentation location must allow tmp_path without retaining either old ban.
    for phrase in ("Tests live in `tests/unit/` (disk only under `tmp_path`, no network or process; run under `clutch.testguard`)",):
        assert phrase in docs
    for phrase in ("no disk, network or process", "avoid disk, network and processes"):
        assert phrase not in docs
