# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Integration pytest setup: wraps each test phase in the I/O guard unless the file is in REAL_IO_TESTS, registers and skips tests marked disk_io_skip, and runs every test in its own empty working directory
# relates: [tests/integration/test_disk_io_skip_list.py, docs/how-clutch-works.md]
# owner: engine
# verified: 403faee1
# hash: eaadb7e758915e0bd5284818330a9eff1cb30f72ddd8531f7a47d2fd77a17860
import pytest

from clutch.ioguard import guard

REAL_IO_TESTS = (
    "test_exec_seam_reap.py",
    "test_exec_seam_unwind_capture.py",
    "test_git.py",
    "test_git_merged_tickets.py",
    "test_git_tree_id.py",
    "test_journal.py",
    "test_journal_duckdb_cache.py",
    "test_journal_incremental.py",
    "test_journal_roll.py",
    "test_lockfile.py",
    "test_mcp_app_dashboard.py",
    "test_mcp_dashboard_wheel.py",
    "test_step_icons.py",
    "test_step_view_unknown_kind.py",
    "test_ui_shared_renderers.py",
)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_setup(item):
    if item.path.name in REAL_IO_TESTS:
        return (yield)
    with guard(item.config._tmp_path_factory.getbasetemp()):
        return (yield)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    if item.path.name in REAL_IO_TESTS:
        return (yield)
    with guard(item.config._tmp_path_factory.getbasetemp()):
        return (yield)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_teardown(item, nextitem):
    if item.path.name in REAL_IO_TESTS:
        return (yield)
    with guard(item.config._tmp_path_factory.getbasetemp()):
        return (yield)


def pytest_configure(config):
    config.addinivalue_line("markers", "disk_io_skip: integration test requires real disk I/O")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.get_closest_marker("disk_io_skip"):
            item.add_marker(pytest.mark.skip(reason="disk-io-skip: writes disk, starts a process, or runs git; rewrite onto the in-memory fakes and remove the disk_io_skip marker from this file"))


@pytest.fixture(autouse=True)
def isolate_working_directory(monkeypatch, tmp_path_factory):
    """Use an explicit fixture repo (e.g. main([...], cwd=repo) or watch_fixture_repo), or anchor tracked reads on Path(__file__).resolve().parents[2]."""
    monkeypatch.chdir(tmp_path_factory.mktemp("integration-cwd"))
