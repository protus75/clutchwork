"""The release audit remains a final, actionable roadmap row."""

from pathlib import Path

from clutch import roadmap


def test_release_audit_row_and_gates():
    text = Path(roadmap.ROADMAP).read_text()
    rows = [row for row in roadmap.parse(text) if roadmap.release_name(row.release) == "0.4.0"]
    last = max(rows, key=lambda row: row.line)
    assert (last.number, last.stem, last.kind, last.priority, last.struck) == (122, "release-audit-040", "chore", "P1", False)
    blocks = roadmap.gates(text)
    assert blocks["0.4.0"][0] == ("uv", "run", "clutch", "roadmap", "merged", "--release", "0.4.0")
    assert blocks["0.4.0"][-2:] == (("./dev.py", "test"), ("uv", "run", "clutch", "roadmap", "accept", "0.4.0"))
    assert blocks["0.4.0"].count(("./dev.py", "test")) == 1
    assert blocks["0.3.0"] == (
        ("uv", "run", "clutch", "roadmap", "merged", "--release", "0.3.0", "--priority", "P0", "P1"),
        ("uv", "run", "clutch", "roadmap", "merged", "docs-truth-sweep", "evidence-envelope"),
        ("uv", "run", "clutch", "roadmap", "merged", "--since", "v0.3.0", "--at-least", "3", "--source", "box:roadmap_row", "--unattended"),
        ("./dev.py", "test"),
        ("uv", "run", "clutch", "roadmap", "accept", "0.3.0"),
    )
    section = text.split("## 9. Keeping this document true", 1)[1]
    assert "stay struck" in section
    assert 'a "Shipped" section' not in section
