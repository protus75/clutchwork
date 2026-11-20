# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test graphics new
# relates: [clutch/__main__.py, clutch/runner.py]
# owner: engine
# verified: 0a308920
# hash: 70310d38f23289cc83725851632a49baf22626d4dde5e768028395e03dea6cc6
import pytest

from clutch.__main__ import _new
from clutch.runner import Refusal


def test_copy_graphics_files(tmp_path):
    (tmp_path / "a.png").write_bytes(b"reference")
    (tmp_path / "b.png").write_bytes(b"input")
    assert _new(tmp_path, "hero", "graphics", (), ["a.png"], ["b.png"]) == 0
    assert (tmp_path / "tickets/hero/reference/a.png").read_bytes() == b"reference"
    assert (tmp_path / "tickets/hero/reference/b.png").read_bytes() == b"input"


def test_reject_invalid_sources_before_writing(tmp_path):
    (tmp_path / "a.png").write_bytes(b"a")
    (tmp_path / "other").mkdir()
    (tmp_path / "other/a.png").write_bytes(b"b")
    (tmp_path / "link.png").symlink_to(tmp_path / "a.png")
    for kind, references, inputs in [("feature", [], ["a.png"]), ("graphics", ["a.png"], ["other/a.png"]), ("graphics", ["link.png"], [])]:
        with pytest.raises(Refusal):
            _new(tmp_path, "hero", kind, (), references, inputs)
        assert not (tmp_path / "tickets/hero").exists()
