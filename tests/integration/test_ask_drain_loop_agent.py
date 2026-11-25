# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the drain-loop prompt delegates Recommendation-driven verdicts, keeps hard limits (no push, no --extension) and limits Suggestion Box triage per tick
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: cd9fb2dc
# hash: 43d89660289cf45a60385fc3aa312800b3391529642041f1f6cf881fff026d3b
import pytest

from clutch import ask
from clutch.config import load_config
from tests.config_helpers import VALID

pytestmark = pytest.mark.disk_io_skip


def render(tmp_path, config_text=VALID):
    (tmp_path / "config.yaml").write_text(config_text)
    return ask.render("drain-loop", "", load_config(None, cwd=tmp_path), tmp_path)


def test_prompt_delegates_recommendations(tmp_path):
    text = render(tmp_path)
    for phrase in (
        "clutch prompt diagnose",
        "clutch prompt drafts",
        "clutch prompt running",
        "clutch ticket confirm --yes",
        "clutch ticket reject --yes",
        "clutch ticket lint",
        "clutch ticket review",
        "clutch box suggest",
        "clutch roadmap status",
        "clutch engine drain --detach",
        "actor: operator",
        "--unattended",
        "rework.md",
        "standing delegation",
        "## Goal / Why",
    ):
        assert phrase in text, f"Omitting {phrase} differs"
    for phrase in ("Never run `confirm` or `reject`", "Needs a human", "never pass `--yes`"):
        assert phrase not in text, f"Retaining {phrase} differs"
    assert text.index("standing delegation") < text.index("clutch ticket confirm --yes")  # A late delegation differs.


def test_prompt_keeps_hard_limits(tmp_path):
    text = render(tmp_path)
    for phrase in (
        "Confirm or reject only by executing a Recommendation",
        "never pass `--extension`",
        "Never push",
        "ticket_changed",
        "docs/roadmap.md",
        "Still open:",
        "no `docs/roadmap.md`",
    ):
        assert phrase in text, f"Omitting {phrase} differs"
    assert "${" not in text  # An unresolved placeholder differs.
    custom = render(tmp_path, VALID.replace("state_dir: .clutch", "state_dir: custom/state"))
    assert "custom/state/drain.out" in custom  # A fixed drain path differs.
    assert "custom/state/engine.log" in custom  # A fixed log path differs.


def test_prompt_bounds_box_triage(tmp_path):
    text = render(tmp_path)
    for phrase in (
        "clutch prompt box",
        "the tick it appears",
        "roadmap_row",
        "clutch box triage",
        "clutch box dismiss",
        "only between drains",
        "once at the end of a phase right before the release gate",
        "unless the owner explicitly asks otherwise",
        "not on every tick",
        "never re-file",
    ):
        assert phrase in text, f"Omitting {phrase} differs"
    for phrase in ("never triage or dismiss", "left for the owner"):
        assert phrase not in text, f"Retaining {phrase} differs"
