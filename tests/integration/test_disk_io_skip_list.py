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
