# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test issue verb
# relates: [clutch/__main__.py, tests/integration/test_cli.py]
# owner: engine
# verified: 148a8874
# hash: 513a5490829ef641b0c23184a42a3ffb0b3aa8a088011b77aa978121153770f4
import importlib.metadata
import platform
from urllib.parse import parse_qs, urlsplit

from clutch.__main__ import main
from tests.integration.test_cli import CONFIG


def test_link_from_installed_metadata(tmp_path, capsys):
    (tmp_path / "body.md").write_text("evidence")
    assert main(["box", "issue", "--class", "engine-stuck", "drain idles", "--body", "body.md"], cwd=tmp_path, env={}) == 0
    out, err = capsys.readouterr()
    repo = next(x.split(", ", 1)[1] for x in importlib.metadata.metadata("clutchwork").get_all("Project-URL") if x.startswith("Repository, "))
    assert out.startswith(repo + "/issues/new?title=%5Bcritical%3Aengine-stuck%5D+drain+idles&body=")
    assert parse_qs(urlsplit(out.strip()).query)["body"][0].endswith(
        "clutchwork " + importlib.metadata.version("clutchwork") + ", Python " + platform.python_version() + ", " + platform.system() + "\nFiled with clutch box issue"
    )
    assert "no secrets were scrubbed" in err


def test_link_scrubs_configured_secret(tmp_path, capsys):
    (tmp_path / "config.yaml").write_text(CONFIG.replace("kind: cli", "kind: cli\n    auth: CLUTCH_ISSUE_KEY"))
    (tmp_path / "body.md").write_text("sk-issue-secret")
    assert main(["box", "issue", "--class", "engine-stuck", "drain idles", "--body", "body.md"], cwd=tmp_path, env={"CLUTCH_ISSUE_KEY": "sk-issue-secret"}) == 0
    out, err = capsys.readouterr()
    assert "sk-issue-secret" not in out
    assert "[REDACTED:CLUTCH_ISSUE_KEY]" in parse_qs(urlsplit(out.strip()).query)["body"][0]
    assert err == ""
