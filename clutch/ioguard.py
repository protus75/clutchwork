"""Block real I/O during integration test phases."""

import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import duckdb


class IntegrationIOBlocked(RuntimeError):
    """An integration test attempted real I/O."""


_basetemp = None
_installed = False


def blocked_operation(event: str, args: tuple, basetemp: Path) -> str | None:
    """Return the operation forbidden by an audit event, if any."""
    if event == "open":
        path, mode, flags = args
        if flags & getattr(os, "O_TMPFILE", 0) == getattr(os, "O_TMPFILE", 0) and getattr(os, "O_TMPFILE", 0):
            return None
        if (mode and any(c in mode for c in "wax+")) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            if isinstance(path, (str, bytes, os.PathLike)) and Path(os.fsdecode(path)).is_dir():
                return None
            return event
    elif event == "os.mkdir":
        if not Path(os.fsdecode(args[0])).resolve().is_relative_to(basetemp.resolve()):
            return event
    elif event in ("os.remove", "os.unlink"):
        path = Path(os.fsdecode(args[0]))
        if path.parent.resolve() == basetemp.resolve() and path.name.endswith("current"):
            return None
        return event
    elif event in (
        "os.rename",
        "os.replace",
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
    ):
        return event
    return None


def _raise(operation):
    raise IntegrationIOBlocked(
        f"{operation} is blocked in integration tests; use the in-memory fakes in tests/fakes.py (FakeFileSystem, FakeExec, FakeJournal) and the shared git fake; only a test of a real I/O function belongs in REAL_IO_TESTS in tests/integration/conftest.py"
    )


def _audit(event, args):
    if _basetemp is not None:
        operation = blocked_operation(event, args, _basetemp)
        if operation:
            _raise(operation)


@contextmanager
def guard(basetemp: Path):
    """Guard a test phase, restoring process state on exit."""
    global _installed, _basetemp
    tempfile.gettempdir()
    if not _installed:
        sys.addaudithook(_audit)
        _installed = True
    original_connect = duckdb.connect

    def connect(database=":memory:", *args, **kwargs):
        if database != ":memory:":
            _raise("duckdb.connect")
        return original_connect(database, *args, **kwargs)

    previous_basetemp = _basetemp
    previous_bytecode = sys.dont_write_bytecode
    with patch.object(duckdb, "connect", connect):
        try:
            _basetemp = basetemp
            sys.dont_write_bytecode = True
            yield
        finally:
            _basetemp = previous_basetemp
            sys.dont_write_bytecode = previous_bytecode
