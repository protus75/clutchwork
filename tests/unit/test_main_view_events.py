# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test main view events
# relates: [clutch/__main__.py, clutch/events.py]
# owner: engine
# verified: bdb23dbf
# hash: 62f93b0d0bf0f31c9303a5a8e7b4571927215365adab9ceb2fde08d7350658fb
from types import SimpleNamespace

import pytest

from clutch import __main__ as entry
from clutch import events


def test_events_parser_and_interrupt(tmp_path, monkeypatch, capsys):
    parser = entry._parser()
    assert parser.parse_args(["view", "events"]).view_verb == "events"  # Dispatching another view differs.
    args = parser.parse_args(["view", "events"])
    assert (args.once, args.cursor, args.timeout) == (False, None, None)
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["view", "events", "--unknown"])
    assert exc.value.code == 2  # Accepting an option differs.
    capsys.readouterr()
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=tmp_path, providers=[]))

    def stop(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(events, "stream", stop)
    assert entry.main(["view", "events"], cwd=tmp_path, env={}) == 0  # Propagating Ctrl-C differs.
    assert capsys.readouterr().err == ""  # Reporting an interrupt as an error differs.
