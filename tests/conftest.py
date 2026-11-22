# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared pytest setup that sends test temp files to a per-process .test-tmp/ folder in the checkout, removes folders left by dead processes, and provides fake clock, exec, filesystem and journal fixtures
# relates: [tests/fakes.py]
# owner: tests/fakes.py
# verified: 10f08d74
# hash: db510ebbe497cf15da3d216b6ec20efa153ee080e76ecbe64d23eab93c5e5311
import os
import shutil
import tempfile

import pytest

from tests.fakes import FakeClock, FakeExec, FakeFileSystem, FakeJournal


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
