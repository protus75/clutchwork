# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that `clutch box issue` builds its link from installed package metadata and scrubs configured secrets from the body.
# relates: [clutch/__main__.py, tests/integration/test_cli.py]
# owner: engine
# verified: ae1a5a3b
# hash: 2024a71456c1c3244999ee23fff244fde433c0ae4fbd799fdf8157e49e826363
import importlib.metadata
import platform
from urllib.parse import parse_qs, urlsplit

import pytest

from clutch.__main__ import main
from tests.cli_helpers import CONFIG

pytestmark = pytest.mark.disk_io_skip


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
