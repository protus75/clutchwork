# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared pytest setup that sends test temp files to a per-process .test-tmp/ folder in the checkout, cleans up folders left by dead processes, and provides fake clock, exec, filesystem, journal and git fixtures
# relates: [tests/fakes.py]
# owner: tests/fakes.py
# verified: b201c27c
# hash: 16df6dd3f318444f6284c071cc97932380659f7c23977069c5ece8d5d67c5f30
import os
import shutil
import tempfile

import pytest

from tests.fakes import FakeClock, FakeExec, FakeFileSystem, FakeGit, FakeJournal


def _reap_dead_pid_dirs(base):
    if not base.exists():
        return
    for entry in base.iterdir():
        if not entry.name.isascii() or not entry.name.isdigit() or not entry.is_dir():
            continue
        try:
            os.kill(int(entry.name), 0)
        except ProcessLookupError:
            shutil.rmtree(entry)
        except PermissionError:
            pass


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    if hasattr(config, "workerinput") or config.option.basetemp is not None:
        return
    base = config.rootpath / ".test-tmp"
    _reap_dead_pid_dirs(base)
    run = base / str(os.getpid())
    temp = run / "tempfile"
    temp.mkdir(parents=True, exist_ok=True)
    config.option.basetemp = str(run / "pytest")
    config._clutch_test_tmp = run
    os.environ["TMPDIR"] = str(temp)
    tempfile.tempdir = str(temp)


def pytest_unconfigure(config):
    run = getattr(config, "_clutch_test_tmp", None)
    if run is not None:
        shutil.rmtree(run)


@pytest.fixture
def fake_clock():
    return FakeClock()


@pytest.fixture
def fake_exec():
    return FakeExec()


@pytest.fixture
def fake_fs():
    return FakeFileSystem()


@pytest.fixture
def fake_journal():
    return FakeJournal()


@pytest.fixture
def fake_git():
    return FakeGit()
