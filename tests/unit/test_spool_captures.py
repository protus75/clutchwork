# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Test the spool capture helper against the production writer.
# relates: [clutch/driver.py, clutch/evidence/store.py, tests/spool_captures.py]
# owner: engine
# verified: 23d3b116
# hash: a633d717d1aca9910567dbca412c7984794077bfdeccea6124985dcbc5276042
import pytest

from clutch.driver import Spool
from clutch.evidence.store import CaptureNotFound, CaptureUnreadable
from clutch.redact import Redactor
from clutch.seams import LocalFileSystem
from tests.spool_captures import list_captures, read_capture, write_capture


@pytest.fixture
def spool(tmp_path):
    return Spool(tmp_path, Redactor({}), LocalFileSystem())


def test_reads_writer_and_separate_runs(tmp_path, spool):
    for stem, attempt, name, text in [("my-ticket", 0, "out", "zero"), ("my-ticket", 2, "out", "two"), ("work/1", 1, "check/verify-01.txt", "first"), ("work/2", 1, "check/verify-01.txt", "second")]:
        spool.write(stem, attempt, name, text)
        assert read_capture(tmp_path, stem, attempt, name) == text.encode()


def test_read_errors(tmp_path, spool):
    spool.write("work", 1, "dir/file", "data")
    with pytest.raises(CaptureNotFound):
        read_capture(tmp_path, "work", 1, "absent")
    with pytest.raises(CaptureNotFound):
        read_capture(tmp_path, "work", 1, "dir")
    (tmp_path / "evidence/captures/work/1/broken.json").write_text("invalid")
    with pytest.raises(CaptureUnreadable):
        read_capture(tmp_path, "work", 1, "broken")


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
    with pytest.raises(ValueError):
        spool.write("item", 0, "run-1/invalid", "data")
    with pytest.raises(ValueError):
        spool.write("item", 0, "bad name", "data")
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


@pytest.fixture
def fake_fs():
    from tests.fakes import FakeFileSystem

    return FakeFileSystem()


def test_fake_round_trip_and_overwrite(tmp_path, fake_fs):
    for stem, attempt in [("my-ticket", 0), ("work/1", 2)]:
        name = "check/verify-01.txt"
        write_capture(tmp_path, stem, attempt, name, b"old", fs=fake_fs)
        # Reject a writer using another slot or changing bytes.
        assert read_capture(tmp_path, stem, attempt, name, fs=fake_fs) == b"old"
        write_capture(tmp_path, stem, attempt, name, b"\x00new\xff", fs=fake_fs)
        # Reject append-only writes and text decoding.
        assert read_capture(tmp_path, stem, attempt, name, fs=fake_fs) == b"\x00new\xff"


def test_fake_read_errors(tmp_path, fake_fs, monkeypatch):
    # Reject raw FileNotFoundError and treating missing captures as unreadable.
    with pytest.raises(CaptureNotFound):
        read_capture(tmp_path, "work", 0, "absent", fs=fake_fs)
    with pytest.raises(CaptureNotFound):
        read_capture(tmp_path, "work", 0, "dir", fs=fake_fs)

    def unreadable(path):
        raise PermissionError(path)

    monkeypatch.setattr(fake_fs, "read_bytes", unreadable)
    # Reject leaking other OS errors or translating them to missing.
    with pytest.raises(CaptureUnreadable):
        read_capture(tmp_path, "work", 0, "denied", fs=fake_fs)


@pytest.mark.parametrize(
    "stem, attempt, name",
    [(stem, 0, "x") for stem in ["", "a/b/c", "Work", None, 5, "work/01", "work/x"]]
    + [("work", attempt, "x") for attempt in [-1, True, "0", 1.0]]
    + [("work", 0, name) for name in ["", "/a", "run-1/a.txt"]],
)
def test_fake_invalid_keys(tmp_path, fake_fs, stem, attempt, name):
    # Reject bypassing capture_key on any seam branch.
    with pytest.raises(ValueError):
        read_capture(tmp_path, stem, attempt, name, fs=fake_fs)
    with pytest.raises(ValueError):
        write_capture(tmp_path, stem, attempt, name, b"data", fs=fake_fs)
    if name == "x":
        with pytest.raises(ValueError):
            list_captures(tmp_path, stem, attempt, fs=fake_fs)
    # Reject filesystem access that creates files or directories before validation.
    assert fake_fs.files == {}
    assert fake_fs.directories == set()


def test_fake_non_bytes(tmp_path, fake_fs):
    with pytest.raises(ValueError):
        write_capture(tmp_path, "work", 0, "x", "text", fs=fake_fs)
    # Reject storing text or creating parents before data validation.
    assert fake_fs.files == {}
    assert fake_fs.directories == set()


def test_fake_listing_matches_disk(tmp_path, fake_fs):
    writers = [Spool(tmp_path, Redactor({}), fs) for fs in (fake_fs, LocalFileSystem())]
    for writer in writers:
        for attempt, name in [(2, "a/x.txt"), (0, "b.txt"), (0, "a/x.txt")]:
            writer.write("item", attempt, name, "data")
        for name in ("run-1/invalid", "bad name"):
            with pytest.raises(ValueError):
                writer.write("item", 0, name, "data")
        writer.write("work", 1, "review/x", "base")
        writer.write("work/1", 0, "review/call-01/prompt.md", "first")
        writer.write("work/2", 0, "review/y", "second")
    # Reject empty, unsorted, unfiltered, or cross-run listings; each expected
    # row has a distinct attempt/name and the disk writer supplies an oracle.
    for stem, attempt in [("item", None), ("item", 2), ("item", 3), ("missing", None), ("work", None), ("work/1", None), ("work/2", None)]:
        assert list_captures(tmp_path, stem, attempt, fs=fake_fs) == list_captures(tmp_path, stem, attempt)


def test_local_filesystem_matches_default(tmp_path):
    fs = LocalFileSystem()
    write_capture(tmp_path, "work/2", 3, "review/out", b"default")
    # Reject a seam reader deriving another layout.
    assert read_capture(tmp_path, "work/2", 3, "review/out", fs=fs) == b"default"
    write_capture(tmp_path, "work/2", 3, "review/out", b"seam", fs=fs)
    assert read_capture(tmp_path, "work/2", 3, "review/out") == b"seam"
    # Reject treating NotADirectoryError from entries(file) as an empty listing.
    assert list_captures(tmp_path, "work/2", fs=fs) == list_captures(tmp_path, "work/2") == [(3, "review/out")]


def test_seam_requires_methods(tmp_path):
    # Reject helper-specific type checks or silently falling back to disk.
    with pytest.raises(AttributeError):
        read_capture(tmp_path, "work", 0, "x", fs=object())
    with pytest.raises(AttributeError):
        write_capture(tmp_path, "work", 0, "x", b"data", fs=object())
    with pytest.raises(AttributeError):
        list_captures(tmp_path, "work", fs=object())
