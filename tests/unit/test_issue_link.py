# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test issue link
# relates: [clutch/__main__.py, clutch/config.py, clutch/issue.py, clutch/observe.py, clutch/redact.py, clutch/runner.py]
# owner: engine
# verified: 0a308920
# hash: a8863829dafedbd335355adb53ced3e90c58963ba8ff473ad11269b2c3360ba6
import platform
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest

from clutch import __main__ as cli
from clutch import issue, observe, runner
from clutch.config import ConfigError
from clutch.redact import Redactor


@pytest.fixture
def metadata(monkeypatch):
    meta = Mock(return_value=SimpleNamespace(get_all=Mock(return_value=["Homepage, https://example.com", "Repository, https://github.com/fork/clutchwork"])))
    ver = Mock(return_value="9.9.9")
    monkeypatch.setattr(observe, "metadata", meta)
    monkeypatch.setattr(issue, "version", ver)
    return meta, ver


def test_link_prefills_only_title_and_body(metadata):
    url = issue.link("state-loss", "journal lost", "Steps:\n1. run `clutch drain`\n\n", lambda text: text)
    body = "Steps:\n1. run `clutch drain`\n\n---\nclutchwork 9.9.9, Python " + platform.python_version() + ", " + platform.system() + "\nFiled with clutch box issue"
    assert url == "https://github.com/fork/clutchwork/issues/new?" + urlencode({"title": "[critical:state-loss] journal lost", "body": body})
    assert set(parse_qs(urlsplit(url).query)) == {"title", "body"}
    metadata[0].assert_called_once_with("clutchwork")
    metadata[1].assert_called_once_with("clutchwork")


def test_classes_are_closed():
    assert issue.CRITICAL == ("state-loss", "secret-leak", "bad-merge", "engine-stuck", "wrong-refusal")
    assert issue.CLASSES == issue.CRITICAL + ("process-gap",)
    for name in ("minor-annoyance", None):
        with pytest.raises(runner.Refusal) as exc:
            issue.link(name, "title", "body", str)
        assert all(x in str(exc.value) for x in issue.CLASSES)
        assert "only a critical bug, or a process gap that cost a real run an attempt or review cycle, is filed upstream; name anything else to the user in chat instead" in str(exc.value)


def test_empty_body_refuses():
    for body in ("", " \n\t"):
        with pytest.raises(runner.Refusal, match="empty"):
            issue.link("state-loss", "title", body, str)


def test_link_length_limit(metadata):
    size = 3000 - len(issue.link("state-loss", "title", "a", str)) + 1
    assert len(issue.link("state-loss", "title", "a" * size, str)) == 3000
    with pytest.raises(runner.Refusal) as exc:
        issue.link("state-loss", "title", "a" * (size + 1), str)
    assert all(x in str(exc.value) for x in ("3001", "3000", "shorten the body; quote only the lines that show the defect"))


def test_secrets_scrubbed_before_encoding(metadata):
    url = issue.link("secret-leak", "s3cr3t value", "s3cr3t value", Redactor({"TOKEN": "s3cr3t value"}).scrub)
    query = parse_qs(urlsplit(url).query)
    assert all("[REDACTED:TOKEN]" in query[key][0] for key in ("title", "body"))
    assert "s3cr3t" not in url


def test_main_prints_link_without_lock_or_writes(metadata, monkeypatch, tmp_path, capsys):
    (tmp_path / "body.md").write_text("s3cr3t")
    load = Mock(return_value=SimpleNamespace(providers=[SimpleNamespace(auth="TOKEN")], release=SimpleNamespace(pypi_token="UV_PUBLISH_TOKEN")))
    monkeypatch.setattr(cli, "load_config", load)
    monkeypatch.setattr(cli, "Lockfile", Mock(side_effect=AssertionError("lock")))
    monkeypatch.setattr(cli, "LocalFileSystem", Mock(side_effect=AssertionError("write")))
    assert cli.main(["box", "issue", "--class", "bad-merge", "merged a red gate", "--body", "body.md"], cwd=tmp_path, env={"TOKEN": "s3cr3t"}) == 0
    out, err = capsys.readouterr()
    assert len(out.splitlines()) == 1 and out.startswith("https://github.com/fork/clutchwork/issues/new?")
    body = parse_qs(urlsplit(out.strip()).query)["body"][0]
    assert "[REDACTED:TOKEN]" in body and "s3cr3t" not in body
    assert err == ""
    load.assert_called_once_with(None, cwd=tmp_path)


def test_main_unscrubbed_when_config_fails(metadata, monkeypatch, tmp_path, capsys):
    (tmp_path / "body.md").write_text("s3cr3t")
    monkeypatch.setattr(cli, "load_config", Mock(side_effect=ConfigError(tmp_path / "config.yaml", None, "config file not found")))
    assert cli.main(["box", "issue", "--class", "state-loss", "title", "--body", "body.md"], cwd=tmp_path, env={}) == 0
    out, err = capsys.readouterr()
    assert "s3cr3t" in parse_qs(urlsplit(out.strip()).query)["body"][0]
    assert len(err.splitlines()) == 1 and "no secrets were scrubbed" in err and "config file not found" in err


def test_main_refusals(metadata, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "load_config", Mock(side_effect=ConfigError(tmp_path / "config.yaml", None, "config file not found")))
    (tmp_path / "invalid").write_bytes(b"\xff\xfe")
    (tmp_path / "empty").write_text("")
    (tmp_path / "large").write_text("a" * 3001)
    (tmp_path / "body").write_text("evidence")
    cases = [("missing", "state-loss"), ("invalid", "state-loss"), ("body", "minor-annoyance"), ("body", None), ("empty", "state-loss"), ("large", "state-loss")]
    for path, cls in cases:
        args = ["box", "issue", *(["--class", cls] if cls else []), "title", "--body", path]
        assert cli.main(args, cwd=tmp_path, env={}) == 2
        out, err = capsys.readouterr()
        assert out == "" and any(line.startswith("clutch box:") for line in err.splitlines())
        if path == "missing":
            assert path in err
    with pytest.raises(SystemExit) as exc:
        cli.main(["box", "issue", "--class", "state-loss", "t"], cwd=tmp_path, env={})
    assert exc.value.code == 2


def test_help_lists_classes(capsys):
    with pytest.raises(SystemExit) as exc:
        cli._parser().parse_args(["box", "issue", "--help"])
    assert exc.value.code == 0
    output = "".join(capsys.readouterr().out.split())
    assert all(name in output for name in issue.CLASSES)
