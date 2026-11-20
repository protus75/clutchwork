"""Keep contention guidance in its host and project rule homes."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Keep contention guidance in its host and project rule homes.
# relates: [clutch/hostfiles.py]
# owner: clutch/hostfiles.py
# verified: 148a8874
# hash: 0a46fee088e4f69afbb3041c57ad8c7fb94b7a53ef9d39a4c57d30a5b0c47013

from pathlib import Path

from clutch import hostfiles

ROOT = Path(__file__).resolve().parents[2]
DO_NOT_GROW = (
    "tests/integration/test_daemon_composition.py",
    "tests/integration/test_drain.py",
    "tests/integration/test_mergequeue.py",
    "tests/integration/test_stages.py",
    "tests/integration/test_cli.py",
    "tests/integration/test_watch.py",
    "tests/integration/serve_rig.py",
)


def test_authoring_guide_states_contention_rules():
    guide = (ROOT / "clutch/docs/host-authoring.md").read_text()
    for phrase in (
        "new test file named for the behavior it covers",
        "in a new module next to its tests",
        "fences only the files its change forces",
        "edits only the section the change makes false",
    ):
        assert phrase in guide
    for path in DO_NOT_GROW:
        assert path not in guide


def test_do_not_grow_list_is_a_repo_rule():
    for name in ("CLAUDE.md", "AGENTS.md"):
        parsed = hostfiles.parse((ROOT / name).read_bytes())
        assert parsed is not None
        project = parsed[1].decode()
        for path in DO_NOT_GROW:
            assert f"`{path}`" in project
        assert "`tests/unit/test_<module>_<behavior>.py`" in project
        assert "`tests/integration/test_<behavior>.py`" in project
    for path in DO_NOT_GROW:
        assert (ROOT / path).is_file()
        assert path.encode() not in hostfiles.CORE_TEMPLATE
