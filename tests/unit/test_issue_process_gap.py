# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test issue process gap
# relates: [clutch/__main__.py, clutch/issue.py, clutch/observe.py]
# owner: engine
# verified: 0a308920
# hash: e0188304035b07afcba78fa6ec24c4c0f042656d95769769be5c8982c25c5470
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

from clutch import __main__ as cli
from clutch import issue, observe


def test_process_gap_title_prefix(monkeypatch):
    monkeypatch.setattr(observe, "repository_url", lambda: "https://example.com/repo")
    url = issue.link("process-gap", "retry skips re-audit", "body", str)
    assert parse_qs(urlsplit(url).query)["title"] == ["[process-gap] retry skips re-audit"]


def test_critical_prefix_unchanged(monkeypatch):
    monkeypatch.setattr(observe, "repository_url", lambda: "https://example.com/repo")
    for name in issue.CRITICAL:
        url = issue.link(name, "t", "body", str)
        assert parse_qs(urlsplit(url).query)["title"] == [f"[critical:{name}] t"]


def test_main_accepts_process_gap(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(observe, "repository_url", lambda: "https://example.com/repo")
    monkeypatch.setattr(cli, "load_config", Mock(return_value=SimpleNamespace(providers=[], release=SimpleNamespace(pypi_token="TOKEN"))))
    (tmp_path / "body.md").write_text("evidence")
    assert cli.main(["box", "issue", "--class", "process-gap", "t", "--body", "body.md"], cwd=tmp_path, env={}) == 0
    out, err = capsys.readouterr()
    assert len(out.splitlines()) == 1 and out.startswith("https://example.com/repo/issues/new?")
    assert parse_qs(urlsplit(out.strip()).query)["title"] == ["[process-gap] t"]
    assert err == ""
