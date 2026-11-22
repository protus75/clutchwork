# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that the DISK_IO_SKIP hook marks only listed files and that the list is sorted, unique, existing and excludes I/O seam tests
# relates: [tests/integration/conftest.py]
# owner: tests/integration/conftest.py
# verified: edd57bac
# hash: 3b2e5319753363c92f4d5ab57393f78072fe9a2e8ef0a942b52ab5fb8bb79cb7
from pathlib import Path
from types import SimpleNamespace

from tests.integration import conftest


class Item:
    def __init__(self, name):
        self.path = Path(name)
        self.markers = []

    def add_marker(self, marker):
        self.markers.append(marker)


def test_hook_marks_only_listed_files():
    listed = Item(conftest.DISK_IO_SKIP[0])
    unlisted = Item("test_disk_io_skip_list.py")
    conftest.pytest_collection_modifyitems(SimpleNamespace(), [listed, unlisted])
    assert len(listed.markers) == 1
    assert listed.markers[0].mark.name == "skip"
    assert listed.markers[0].mark.kwargs["reason"].startswith("disk-io-skip:")
    assert unlisted.markers == []


def test_skip_list_is_sorted_unique_existing_and_excludes_io_functions():
    names = conftest.DISK_IO_SKIP
    assert names == tuple(sorted(names))
    assert len(names) == len(set(names))
    assert all((Path(__file__).parent / name).is_file() for name in names)
    assert not set(names) & {
        "test_git.py",
        "test_git_tree_id.py",
        "test_git_merged_tickets.py",
        "test_journal.py",
        "test_journal_duckdb_cache.py",
        "test_journal_incremental.py",
        "test_journal_roll.py",
        "test_lockfile.py",
        "test_exec_seam_reap.py",
        "test_exec_seam_unwind_capture.py",
    }
