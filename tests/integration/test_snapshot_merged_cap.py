# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that `view snapshot` caps merged rows at the configured snapshot_merged_limit and shows all of them with --all-merged. Also tests that the config loader refuses a zero limit.
# relates: [clutch/__main__.py, clutch/config.py, tests/integration/test_config.py, tests/integration/test_drain.py, tests/snapshot_scale_fixture.py]
# owner: clutch/observe.py
# verified: d32c32ad
# hash: 177487cbc37bb8f4b30fbd25f99d875751f91567b4e89a3701f2c8baf42ad50f
import json
import os

import pytest

from clutch import __main__ as entry
from clutch.config import ConfigError, load_config
from tests.integration.test_config import VALID
from tests.integration.test_drain import confirmed
from tests.snapshot_scale_fixture import git

pytestmark = pytest.mark.disk_io_skip


def test_cli_cap_and_config(tmp_path, capsys):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "Fixture")
    git(tmp_path, "config", "user.email", "fixture@example.com")
    config = tmp_path / "config.yaml"
    config.write_text(VALID)
    assert load_config(config, cwd=tmp_path).snapshot_merged_limit == 100
    config.write_text(VALID + "\nsnapshot_merged_limit: 0\n")
    with pytest.raises(ConfigError, match="snapshot_merged_limit"):
        load_config(config, cwd=tmp_path)
    config.write_text(VALID + "\nsnapshot_merged_limit: 2\n")
    for i in range(5):
        path = tmp_path / "tickets" / f"item-{i}" / "ticket.md"
        path.parent.mkdir(parents=True)
        path.write_text(confirmed())
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "tickets")
    sha = git(tmp_path, "rev-parse", "HEAD")
    journal = tmp_path / ".clutch/journal/000001-20260804.jsonl"
    journal.parent.mkdir(parents=True)
    journal.write_text(
        "".join(json.dumps(dict(v=1, type="state_transition", ts=f"2026-08-0{i + 1}T12:00:00+00:00", ticket=f"item-{i}", key=None, body={"to": "merged", "commit": sha})) + "\n" for i in range(5))
    )
    for flag, expected in (([], 2), (["--all-merged"], 5)):
        assert entry.main(["--config", str(config), "view", "snapshot", *flag], cwd=tmp_path, env=os.environ) == 0
        output = json.loads(capsys.readouterr().out)
        assert sum(row["section"] == "merged" for row in output["rows"]) == expected
