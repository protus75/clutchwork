# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests checking that tmp_path and tempfile land in the checkout's .test-tmp/, that cleanup removes only dead-PID folders, that an explicit basetemp is left alone, and that unconfigure removes only this run's folder
# relates: [tests/conftest.py]
# owner: tests/conftest.py
# verified: b201c27c
# hash: d4f75ca7cedeeadfc5cb4c361ac0eb5ad284815b86adeb752cae80ef6ab96a93
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

from tests.conftest import _reap_dead_pid_dirs, pytest_configure, pytest_unconfigure

CHECKOUT_TEMP = Path(__file__).resolve().parents[2] / ".test-tmp"


def test_tmp_path_is_in_checkout(tmp_path):
    assert tmp_path.resolve().is_relative_to(CHECKOUT_TEMP)


def test_tempfile_first_use_is_in_checkout():
    with tempfile.TemporaryDirectory() as directory:
        assert Path(directory).resolve().is_relative_to(CHECKOUT_TEMP)
        assert Path(tempfile.gettempdir()).resolve().is_relative_to(CHECKOUT_TEMP)


def test_reaper_keeps_live_and_non_numeric_directories(tmp_path):
    pid = 2**30
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        except PermissionError:
            pass
        pid -= 1
    dead = tmp_path / str(pid)
    live = tmp_path / str(os.getpid())
    other = tmp_path / "keep-me"
    for path in (dead, live, other):
        path.mkdir()
    _reap_dead_pid_dirs(tmp_path)
    assert not dead.exists()
    assert live.is_dir()
    assert other.is_dir()


def test_explicit_basetemp_is_untouched(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "tempdir", tempfile.tempdir)
    monkeypatch.setenv("TMPDIR", os.environ.get("TMPDIR", ""))
    explicit = str(tmp_path / "explicit")
    config = SimpleNamespace(rootpath=tmp_path, option=SimpleNamespace(basetemp=explicit))
    pytest_configure(config)
    pytest_unconfigure(config)
    assert config.option.basetemp == explicit
    assert not (tmp_path / ".test-tmp").exists()


def test_unconfigure_removes_only_own_run(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "tempdir", tempfile.tempdir)
    monkeypatch.setenv("TMPDIR", os.environ.get("TMPDIR", ""))
    sibling = tmp_path / ".test-tmp" / "keep-me"
    sibling.mkdir(parents=True)
    config = SimpleNamespace(rootpath=tmp_path, option=SimpleNamespace(basetemp=None))
    pytest_configure(config)
    run = tmp_path / ".test-tmp" / str(os.getpid())
    assert (run / "tempfile").is_dir()
    assert config.option.basetemp == str(run / "pytest")
    pytest_unconfigure(config)
    assert not run.exists()
    assert sibling.is_dir()
