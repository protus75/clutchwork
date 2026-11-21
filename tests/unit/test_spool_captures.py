# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Test the spool capture helper against the production writer.
# relates: [clutch/driver.py, clutch/evidence/store.py, tests/spool_captures.py]
# owner: engine
# verified: e3a6f154
# hash: da7c9d383a44b195b6b7d5ade3cb9e30b4751e2f984b6f6d6f5fc1a771bd9d2a
import pytest

from clutch.driver import Spool
from clutch.evidence.store import CaptureNotFound, CaptureUnreadable
from clutch.redact import Redactor
from clutch.seams import LocalFileSystem
from tests.spool_captures import list_captures, read_capture, write_capture


@pytest.fixture
def spool(tmp_path):
    return Spool(tmp_path / "spools", Redactor({}), LocalFileSystem())


def test_reads_writer_and_separate_runs(tmp_path, spool):
    for stem, attempt, name, text in [("my-ticket", 0, "out", "zero"), ("my-ticket", 2, "out", "two"), ("work/1", 1, "check/verify-01.txt", "first"), ("work/2", 1, "check/verify-01.txt", "second")]:
        spool.write(stem, attempt, name, text)
        assert read_capture(tmp_path, stem, attempt, name) == text.encode()


def test_read_errors(tmp_path, spool):
    spool.write("work", 1, "dir/file", "data")
    with pytest.raises(CaptureNotFound):
        read_capture(tmp_path, "work", 1, "absent")
    with pytest.raises(CaptureUnreadable):
        read_capture(tmp_path, "work", 1, "dir")


@pytest.mark.parametrize("stem", ["", "a/b/c", "Work", None, 5, "work/01", "work/x"])
def test_invalid_stem(tmp_path, stem):
    state = tmp_path / "absent"
    with pytest.raises(ValueError):
        read_capture(state, stem, 0, "x")
    with pytest.raises(ValueError):
        list_captures(state, stem)
    with pytest.raises(ValueError):
        write_capture(state, stem, 0, "x", b"data")
    assert not state.exists()


@pytest.mark.parametrize("attempt", [-1, True, "0", 1.0])
def test_invalid_attempt(tmp_path, attempt):
    state = tmp_path / "absent"
    with pytest.raises(ValueError):
        read_capture(state, "work", attempt, "x")
    with pytest.raises(ValueError):
        list_captures(state, "work", attempt)
    with pytest.raises(ValueError):
        write_capture(state, "work", attempt, "x", b"data")
    assert not state.exists()


@pytest.mark.parametrize("name", ["", "/a", "run-1/a.txt"])
def test_invalid_name(tmp_path, name):
    state = tmp_path / "absent"
    with pytest.raises(ValueError):
        read_capture(state, "work", 0, name)
    with pytest.raises(ValueError):
        write_capture(state, "work", 0, name, b"data")
    assert not state.exists()


def test_write_bytes_and_overwrite(tmp_path):
    for stem, attempt in [("my-ticket", 0), ("work/1", 1)]:
        write_capture(tmp_path, stem, attempt, "check/verify-01.txt", b"old")
        write_capture(tmp_path, stem, attempt, "check/verify-01.txt", b"\x00new\xff")
        assert read_capture(tmp_path, stem, attempt, "check/verify-01.txt") == b"\x00new\xff"
    state = tmp_path / "absent"
    with pytest.raises(ValueError):
        write_capture(state, "work", 0, "x", "text")
    assert not state.exists()


def test_listing(tmp_path, spool):
    for attempt, name in [(2, "a/x.txt"), (0, "b.txt"), (0, "a/x.txt")]:
        spool.write("item", attempt, name, "data")
    spool.write("item", 0, "run-1/invalid", "data")
    spool.write("item", 0, "bad name", "data")
    (tmp_path / "spools/item/nope").mkdir()
    assert list_captures(tmp_path, "item") == [(0, "a/x.txt"), (0, "b.txt"), (2, "a/x.txt")]
    assert list_captures(tmp_path, "item", 2) == [(2, "a/x.txt")]
    assert list_captures(tmp_path, "item", 3) == []
    assert list_captures(tmp_path, "missing") == []


def test_listing_overlapping_runs(tmp_path, spool):
    spool.write("work", 1, "review/x", "base")
    spool.write("work/1", 0, "review/call-01/prompt.md", "first")
    spool.write("work/2", 0, "review/y", "second")
    assert list_captures(tmp_path, "work") == [(1, "review/x")]
    assert list_captures(tmp_path, "work/1") == [(0, "review/call-01/prompt.md")]
    assert list_captures(tmp_path, "work/2") == [(0, "review/y")]
