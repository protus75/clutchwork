"""Exercise integration I/O decisions and their audit hook."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the integration I/O guard: which file, directory, process, socket and DuckDB operations it blocks or allows, and that guard() restores state on exit
# relates: [clutch/ioguard.py]
# owner: clutch/ioguard.py
# verified: d6229699
# hash: ee7230065670065fc2111dd72a8c8869a41261e4fdd4b8e9f24694a2dca06dd2

import os
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

import duckdb
import pytest

from clutch.ioguard import IntegrationIOBlocked, blocked_operation, guard

_EXECUTE_CHILD = subprocess.Popen._execute_child


@pytest.mark.parametrize("mode", ["w", "a", "x"])
def test_open_blocked(tmp_path, mode):
    target = tmp_path / "file"
    with guard(tmp_path), pytest.raises(IntegrationIOBlocked, match="tests/fakes.py.*REAL_IO_TESTS"):
        open(target, mode)
    assert not target.exists()


def test_other_operations_blocked(tmp_path):
    source = tmp_path / "source"
    source.write_text("original")
    directory = tmp_path / "directory"
    directory.mkdir()
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    targets = [tmp_path / "created", tmp_path / "renamed", outside, tmp_path / "db.duckdb"]
    actions = [
        lambda: os.open(targets[0], os.O_WRONLY | os.O_CREAT),
        lambda: os.rename(source, targets[1]),
        lambda: os.remove(source),
        lambda: shutil.rmtree(directory),
        lambda: os.mkdir(outside),
        lambda: duckdb.connect(str(targets[3])),
    ]
    for action in actions:
        with guard(tmp_path), pytest.raises(IntegrationIOBlocked):
            action()
    with patch.object(subprocess.Popen, "_execute_child", _EXECUTE_CHILD):
        with guard(tmp_path), pytest.raises(IntegrationIOBlocked):
            subprocess.Popen(["true"])
    assert source.read_text() == "original"
    assert directory.is_dir()
    assert all(not target.exists() for target in targets)


def test_allowed_and_restored(tmp_path, tmp_path_factory):
    source = tmp_path / "source"
    source.write_text("content")
    previous = sys.dont_write_bytecode
    with guard(tmp_path_factory.getbasetemp()):
        assert sys.dont_write_bytecode is True
        assert source.read_text() == "content"
        os.mkdir(tmp_path / "d")
        assert duckdb.connect(":memory:").execute("select 42").fetchone() == (42,)
        assert duckdb.connect().execute("select 43").fetchone() == (43,)
        tmp_path_factory.mktemp("same")
        tmp_path_factory.mktemp("same")
        with tempfile.TemporaryFile() as f:
            f.write(b"capture")
            f.seek(0)
            assert f.read() == b"capture"
    assert sys.dont_write_bytecode == previous
    (tmp_path / "g").write_text("after")
    assert (tmp_path / "g").read_text() == "after"
    assert (tmp_path / "d").is_dir()


@pytest.mark.parametrize("mode,flags", [("w", 0), ("a", 0), ("x", 0), (None, os.O_CREAT), (None, os.O_EXCL | os.O_CREAT), (None, os.O_WRONLY)])
def test_open_decisions(tmp_path, mode, flags):
    assert blocked_operation("open", (str(tmp_path / "file"), mode, flags), tmp_path) == "open"


def test_open_exceptions(tmp_path):
    assert blocked_operation("open", (str(tmp_path / "file"), "r", os.O_RDONLY), tmp_path) is None
    assert blocked_operation("open", (str(tmp_path), "w+", os.O_CREAT), tmp_path) is None
    assert blocked_operation("open", (str(tmp_path), None, os.O_TMPFILE | os.O_RDWR), tmp_path) is None


@pytest.mark.parametrize(
    "event",
    [
        "os.rename",
        "os.replace",
        "os.remove",
        "os.unlink",
        "os.rmdir",
        "shutil.copyfile",
        "shutil.copytree",
        "shutil.move",
        "shutil.rmtree",
        "subprocess.Popen",
        "os.system",
        "os.posix_spawn",
        "os.exec",
        "socket.connect",
    ],
)
def test_blocked_events(tmp_path, event):
    assert blocked_operation(event, (str(tmp_path / "ordinary"),), tmp_path) == event


def test_directory_and_current_decisions(tmp_path):
    assert blocked_operation("os.mkdir", (str(tmp_path / "inside"),), tmp_path) is None
    assert blocked_operation("os.mkdir", (str(tmp_path.parent / "outside"),), tmp_path) == "os.mkdir"
    for event in ("os.remove", "os.unlink"):
        assert blocked_operation(event, (str(tmp_path / "samecurrent"),), tmp_path) is None
        assert blocked_operation(event, (str(tmp_path / "nested" / "samecurrent"),), tmp_path) == event
    assert blocked_operation("unrelated", (), tmp_path) is None
