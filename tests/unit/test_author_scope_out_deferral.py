from types import SimpleNamespace

import pytest

from clutch import author


@pytest.mark.parametrize(
    "phrase",
    [
        "separate tickets",
        "separate ticket",
        "follow-up tickets",
        "follow-up ticket",
        "follow-up rows",
        "follow-up row",
        "later tickets",
        "later ticket",
        "future tickets",
        "future ticket",
        "another ticket",
        "other tickets",
    ],
)
def test_deferral_requires_follow_up(tmp_path, phrase):
    text = f"The writer and the lock are {phrase} and out of scope."
    findings = author.deferral_follow_up(object(), text, ("clutch/author.py",), tmp_path)
    assert len(findings) == 1
    assert findings[0].code == author.AuthorGate.code
    assert "docs/roadmap.md" in findings[0].paved_road
    assert "backticks" in findings[0].paved_road
    assert "whole row" in findings[0].paved_road
    assert author.deferral_follow_up(object(), text, ("docs/roadmap.md",), tmp_path) == []
    assert author.deferral_follow_up(None, text, (), tmp_path) == []


def test_existing_backticked_stem_resolves_deferral(tmp_path):
    text = "Out: separate tickets, including `writer-fix`."
    ticket = tmp_path / "tickets/writer-fix/ticket.md"
    ticket.parent.mkdir(parents=True)
    assert len(author.deferral_follow_up(object(), text, (), tmp_path)) == 1
    ticket.write_text("ticket")
    assert author.deferral_follow_up(object(), text, (), tmp_path) == []
    assert len(author.deferral_follow_up(object(), text.replace("`", ""), (), tmp_path)) == 1
    assert author.deferral_follow_up(object(), "Out: lint and roadmap parsing.", (), tmp_path) == []


def test_gate_checks_scope_and_fence(tmp_path, monkeypatch):
    row = SimpleNamespace(stem="sample-row", kind="feature", priority="P1")
    gate = author.AuthorGate(SimpleNamespace(repo=tmp_path, journal=SimpleNamespace(read=lambda: [])))
    gate.message = SimpleNamespace(roadmap_row=row, report=None)
    scope = "The writer and the lock are separate tickets and out of scope."
    parsed = SimpleNamespace(frontmatter=SimpleNamespace(kind="feature", priority="P1"), sections={"Scope in / Scope out": scope}, scope_fence=("clutch/author.py",))
    monkeypatch.setattr(author, "validate_ticket", lambda *args: parsed)
    reply = author.AuthorReply(stem="sample-row", ticket=f"## Scope in / Scope out\n{scope}")
    report = gate.check(reply, tmp_path)
    assert report.verdict == "fail"
    assert len(report.findings) == 1
    parsed.scope_fence = ("docs/roadmap.md",)
    assert gate.check(reply, tmp_path).verdict == "pass"
