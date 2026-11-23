"""The installed authoring guide states the lint rules."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the installed authoring guide states each ticket lint rule, such as cycle refusal, criteria backticks, main...HEAD diffs and time budget splits
# relates: [clutch/docs/host-authoring.md, clutch/tickets.py]
# owner: clutch/docs/host-authoring.md
# verified: 981eb002
# hash: e8e7d952db49972210ea55b9c3328d3b9f46193a255341b0c332a8f2cefe9d53

from pathlib import Path


def test_guide_states_lint_rules():
    guide = (Path(__file__).resolve().parents[2] / "clutch/docs/host-authoring.md").read_text()
    for phrase in (
        "never close a cycle",
        "never list a prompt spec in `Context`",
        "an `On-demand` path is fenced and never also in `Context`",
        "refused as unmeasurable",
        "every criterion names a check in backticks",
        "A changed-files check against main uses `main...HEAD`, never `main`",
        "`stuck` is twice `expected`",
        "over 60m, always split into more tickets, each its own stem",
        "Over 30m, split when possible or add `- reason: <why it is not split>`",
        "`## Regression` appears only in a `kind: bug` ticket",
        "a bumped prompt spec needs a fenced test pin",
        "a document named in `Scope in` is fenced",
        "a stem with no `tickets/<stem>/ticket.md` is refused",
    ):
        assert phrase in guide
