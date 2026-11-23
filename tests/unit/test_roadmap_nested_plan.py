"""Nested roadmap plan resolution and selection."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for roadmap plan_path and choose resolving nested docs/<name>/plan.md plans, ambiguity with flat plans, and wait-road wording.
# relates: [clutch/roadmap.py]
# owner: clutch/roadmap.py
# verified: 832f8056
# hash: 27abbe9340421833d21462b285157dd1a71060a1a002d614790ac91d22739659

import pytest

from clutch.roadmap import choose, parse, plan_path

FILES = {"docs/document-agent/plan.md", "docs/roadmap.md"}


@pytest.mark.parametrize("owner", ["document plan 1", "document-agent plan"])
def test_nested_plan_matches_directory(owner):
    assert plan_path(owner, FILES) == "docs/document-agent/plan.md"


def test_nested_and_flat_matches_are_ambiguous():
    assert plan_path("document plan", FILES | {"docs/document-extra-plan.md"}) is None


@pytest.mark.parametrize("owner", ["document plan 1", "document plan 2", "document plan 3", "document-agent plan"])
def test_choose_readies_rows_with_nested_plan(owner):
    rows = parse(
        "### 0.7.0\n"
        "| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n"
        "|---|---|---|---|---|---|---|---|\n"
        f"| 75 | `document-work` | {owner} | feature | P1 | `prerequisite` | | Work. |\n"
    )
    choice = choose(rows, states={"prerequisite": "merged"}, files=FILES)
    assert choice.ready == tuple(rows)
    assert not any(wait.reason.startswith("no unique plan") for wait in choice.waits)


def test_wait_names_both_plan_forms():
    rows = parse(
        "### 0.7.0\n| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n|---|---|---|---|---|---|---|---|\n| 75 | `document-work` | document plan | feature | P1 | | | Work. |\n"
    )
    road = choose(rows, states={}, files=set()).waits[0].road
    assert "docs/*-plan.md" in road and "docs/<name>/plan.md" in road
