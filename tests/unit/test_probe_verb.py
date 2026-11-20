# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test probe verb
# relates: [clutch/__main__.py, clutch/config.py]
# owner: engine
# verified: 9a610809
# hash: c6b1618794fd0cf5381e57d4b913e93e3d24e16258f961bff01109c65a872438
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from clutch import __main__ as cli
from clutch.config import Limits, ModelsByTier, Provider


def test_probe(monkeypatch, capsys):
    def provider(name, model):
        return Provider(name=name, kind="cli", package="pkg", models_by_tier=ModelsByTier(low=model, medium=model, high=model, max=model), limits=Limits(concurrency=1, est_cost_per_call_usd=1))

    config = SimpleNamespace(release=SimpleNamespace(pypi_token="UV_PUBLISH_TOKEN"), providers=[provider("claude", "opus"), provider("codex", "gpt")], state_dir=Path("/state"))
    monkeypatch.setattr(cli, "load_config", lambda *a, **k: config)
    monkeypatch.setattr(cli, "Lockfile", Mock(side_effect=AssertionError("lock")))
    monkeypatch.setattr(cli, "Journal", Mock(side_effect=AssertionError("journal")))
    fs = Mock()
    fs.entries.return_value = []
    monkeypatch.setattr(cli, "LocalFileSystem", lambda: fs)

    class Exec:
        async def run(self, argv, **kwargs):
            if argv[0] == "codex":
                return 1, "", "model not found"
            return 0, json.dumps({"type": "result", "subtype": "success", "result": "ok", "total_cost_usd": 0.5}), ""

    monkeypatch.setattr(cli, "SubprocessExec", Exec)
    assert cli.main(["provider", "probe", "claude"], cwd=Path("/repo"), env={}) == 0
    assert "claude opus: ok" in capsys.readouterr().out
    assert cli.main(["provider", "probe"], cwd=Path("/repo"), env={}) == 1
    out = capsys.readouterr().out
    assert "claude opus: ok" in out and "codex gpt:" in out and "fix provider 'codex'" in out
    assert cli.main(["provider", "probe", "missing"], cwd=Path("/repo"), env={}) == 2
    assert "claude" in capsys.readouterr().err
