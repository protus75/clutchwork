# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Guard rendered metadata against trailing whitespace.
# relates: [clutch/meta.py, tests/unit/test_meta_refresh.py]
# owner: engine
# verified: bba3321b
# hash: 164f1d6680f1c155f7531999566da22b2d28c1fabc92ca6c7f4d26239fc396e5
from pathlib import Path

import pytest

from clutch import meta
from tests.unit.test_meta_refresh import MemoryFS, config, run


@pytest.mark.parametrize("path,body", [("tests/a.py", "value = 42\n"), ("docs/a.md", "A body.\n")])
def test_refresh_has_no_trailing_whitespace_and_round_trips(path, body):
    fs = MemoryFS({path: body})
    run(fs, [path])
    text = fs.read_bytes(Path("/repo") / path).decode()
    assert all(line == line.rstrip() for line in text.splitlines())
    fields, restored, _ = meta.parse(text, Path(path).suffix)
    assert fields["purpose"] == ""
    assert restored == body
    assert meta.check(config(), Path("/repo"), fs, [path], "123456789") == [(path, "empty_purpose")]


def test_nonempty_purpose_keeps_one_space():
    path = "tests/a.py"
    fs = MemoryFS({path: "value = 42\n"})
    run(fs, [path])
    file = Path("/repo") / path
    fs.files[file] = fs.files[file].replace(b"# purpose:\n", b"# purpose: useful\n")
    run(fs, [path])
    assert b"# purpose: useful\n" in fs.read_bytes(file)
