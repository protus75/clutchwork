# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that the conftest hook skips only disk_io_skip-marked items, that real-I/O test files carry no skip marker, and that the old DISK_IO_SKIP list is gone.
# relates: [tests/integration/conftest.py]
# owner: tests/integration/conftest.py
# verified: d32c32ad
# hash: 40e463ace65efd7993003f84c61b7eb71c5e7bb39b228d849cac5d0cd6713653
import re
from pathlib import Path
from types import SimpleNamespace

from tests.integration import conftest


class Item:
    def __init__(self, marked):
        self.marked = marked
        self.markers = []

    def get_closest_marker(self, name):
        assert name == "disk_io_skip"
        return object() if self.marked else None

    def add_marker(self, marker):
        self.markers.append(marker)


def test_hook_marks_only_marked_items():
    marked = Item(True)
    unmarked = Item(False)
    conftest.pytest_collection_modifyitems(SimpleNamespace(), [marked, unmarked])
    assert len(marked.markers) == 1
    assert marked.markers[0].mark.name == "skip"
    assert marked.markers[0].mark.kwargs["reason"].startswith("disk-io-skip:")
    assert unmarked.markers == []


def test_real_io_files_have_no_skip_marker_and_list_is_removed():
    pattern = re.compile(r"^pytestmark = pytest\.mark\.disk_io_skip$", re.MULTILINE)
    marked = {path.name for path in Path(__file__).parent.glob("test_*.py") if pattern.search(path.read_text())}
    assert not marked.intersection(conftest.REAL_IO_TESTS)
    assert not hasattr(conftest, "DISK_IO_SKIP")
