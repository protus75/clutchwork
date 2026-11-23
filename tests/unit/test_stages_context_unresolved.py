# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that implement_inputs swaps a Python context selector matching zero or several definitions for a read-the-file notice, leaves other context entries unchanged, and still raises on undecodable or missing context files.
# relates: [clutch/stages.py]
# owner: clutch/stages.py
# verified: 7e251619
# hash: 0d25a598ce3a6b3b0bb7148d12b3c404bf5130c20c0895561352e6f686c3cdbb
from types import SimpleNamespace

import pytest

from clutch.stages import implement_inputs


@pytest.mark.parametrize("source", ["def present():\n    pass\n", "def gone():\n    pass\ndef gone():\n    pass\n"])
def test_unresolved_selector_keeps_notice_and_other_context(tmp_path, source):
    (tmp_path / "a.py").write_text(source)
    (tmp_path / "b.md").write_text("# Full document\nSome text.\n")
    ticket = SimpleNamespace(context=("a.py::gone", "b.md"))

    context = implement_inputs(tmp_path, "ticket", ticket, ())["context"]

    # Wrong: raising, choosing a duplicate, dropping the notice, or changing the other entry.
    assert context == (
        "### a.py::gone\n(selector does not resolve in this worktree: Python selector 'gone' must match exactly one definition; read the file directly)\n\n### b.md\n# Full document\nSome text.\n"
    )


def test_context_decode_error_escapes(tmp_path):
    (tmp_path / "a.py").write_bytes(b"\xff")
    ticket = SimpleNamespace(context=("a.py::gone",))

    # Wrong: treating a file decoding failure as a selector resolution failure.
    with pytest.raises(UnicodeDecodeError):
        implement_inputs(tmp_path, "ticket", ticket, ())


def test_missing_context_file_escapes(tmp_path):
    ticket = SimpleNamespace(context=("missing.py::gone",))

    # Wrong: turning a missing file into a selector notice.
    with pytest.raises(FileNotFoundError):
        implement_inputs(tmp_path, "ticket", ticket, ())
