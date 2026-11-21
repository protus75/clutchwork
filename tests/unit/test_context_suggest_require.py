# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: require selectors for context suggestions
# relates: [clutch/__main__.py, clutch/context.py]
# owner: engine
# verified: 188365c9
# hash: 8ff786dcb1935b01e17d058909aec0dc29ec79148123af4c54898606fa553e9a
from pathlib import Path
from types import SimpleNamespace

from clutch import context
from clutch.__main__ import _run_context_suggest


class FS:
    def read_bytes(self, path):
        return b"## Goal / Why\ntext\n## Scope fence\n- file\n"

    def size(self, path):
        return 1


class Connection:
    def close(self):
        pass


def test_require_empty_and_suggested(monkeypatch, capsys):
    config = SimpleNamespace(state_dir=Path("/state"))
    monkeypatch.setattr(context, "suggest", lambda *args: ([], []))

    def run():
        return _run_context_suggest(config, Path("/repo"), "demo", fs=FS(), connect=lambda *args, **kwargs: Connection(), require=True)

    assert run() == 1
    assert capsys.readouterr().out == "context suggest: none\n"
    monkeypatch.setattr(context, "suggest", lambda *args: ([("other", "related")], []))
    assert run() == 0
    assert capsys.readouterr().out == "context suggest: suggested\n- other  # related\n"
