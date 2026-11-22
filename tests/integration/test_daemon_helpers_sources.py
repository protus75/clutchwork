"""Read-only evidence that the shared source helpers follow production imports."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Read-only tests that the shared sources, import_closure and without_core_import helpers read every clutch module and follow production imports, so removing the core import cuts clutch.daemon from the __main__ closure.
# relates: [tests/daemon_helpers.py]
# owner: tests/daemon_helpers.py
# verified: f98b9306
# hash: 7f5bb07a06ff0bc6718bc6a8e1336cd0ee5375fdf7003e5c088e9a59ce8c640b

from pathlib import Path

import pytest

from tests.daemon_helpers import import_closure, sources, without_core_import


def test_sources():
    material = sources()
    root = Path(__file__).resolve().parents[2]
    expected = {".".join(path.relative_to(root).with_suffix("").parts) for path in (root / "clutch").rglob("*.py")}
    expected.remove("clutch.__init__")
    expected.add("clutch")
    # Rules out using the old hub anchor, missing nested modules, or keeping __init__ as the package name.
    assert (set(material), material["clutch.__main__"]) == (expected, (root / "clutch/__main__.py").read_text())


def test_source_import_closure_without_core():
    material = sources()
    reached = import_closure("clutch.__main__", material)
    removed = without_core_import(material)
    # Rules out a no-op transformer or a closure that returns all source modules.
    assert ("clutch.daemon" in reached, "clutch.daemon" in import_closure("clutch.__main__", removed)) == (True, False)
