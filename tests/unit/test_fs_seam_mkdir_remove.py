from datetime import UTC, datetime

from clutch.enginelog import EngineLog
from clutch.journal import EventType, Journal
from clutch.redact import Redactor
from clutch.seams import LocalFileSystem


def clock():
    return datetime(2026, 8, 4, tzinfo=UTC)


def test_mkdir_creates_parents_and_is_idempotent(tmp_path):
    path = tmp_path / "a" / "b"
    fs = LocalFileSystem()
    fs.mkdir(path)
    assert path.is_dir()
    fs.mkdir(path)
    assert path.is_dir()


def test_remove_deletes_file_and_tolerates_absent(tmp_path):
    path = tmp_path / "present"
    path.write_text("data")
    fs = LocalFileSystem()
    fs.remove(path)
    assert not path.exists()
    assert fs.remove(tmp_path / "never") is None


def test_enginelog_creates_missing_directory(tmp_path):
    path = tmp_path / "deep" / "engine.log"
    EngineLog(path, Redactor({}), clock).event("example")
    assert len(path.read_text().splitlines()) == 1


def test_journal_append_creates_state_dir(tmp_path):
    journal = Journal(tmp_path / "state", clock)
    event = journal.append(EventType.EFFECT_INTENT, {"example": "value"})
    assert journal.read() == [event]
