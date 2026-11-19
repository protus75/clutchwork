from types import SimpleNamespace

import pytest

from clutch import __main__ as entry
from clutch import events


def test_events_parser_and_interrupt(tmp_path, monkeypatch, capsys):
    parser = entry._parser()
    assert parser.parse_args(["view", "events"]).view_verb == "events"  # Dispatching another view differs.
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["view", "events", "--once"])
    assert exc.value.code == 2  # Accepting an option differs.
    capsys.readouterr()
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=tmp_path, providers=[]))

    def stop(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(events, "stream", stop)
    assert entry.main(["view", "events"], cwd=tmp_path, env={}) == 0  # Propagating Ctrl-C differs.
    assert capsys.readouterr().err == ""  # Reporting an interrupt as an error differs.
