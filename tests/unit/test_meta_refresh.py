from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import meta


class MemoryFS:
    def __init__(self, files):
        self.files = {Path("/repo") / p: v.encode() for p, v in files.items()}
        self.writes = []

    def read_bytes(self, path):
        return self.files[path]

    def write(self, path, data):
        self.files[path] = data
        self.writes.append(path)


def config():
    return SimpleNamespace(meta=SimpleNamespace(paths=[SimpleNamespace(root="docs/", kind="plan"), SimpleNamespace(root="tests/", kind="test")]))


def run(fs, files, sha="123456789"):
    return meta.refresh(config(), Path("/repo"), fs, files, sha)


@pytest.mark.parametrize("body", ["# comment\nvalue = 1\n", '"""doc"""\n# comment\nvalue = 1\n'])
def test_python_comments_and_idempotence(body):
    fs = MemoryFS({"tests/a.py": body})
    assert run(fs, ["tests/a.py"]) == (["tests/a.py"], [])
    text = fs.read_bytes(Path("/repo/tests/a.py")).decode()
    fields, restored, _ = meta.parse(text, ".py")
    assert restored == body and fields["purpose"] == ""
    if body.startswith('"""doc"""'):
        assert text.startswith('"""doc"""\n# clutch:meta\n')
    assert run(fs, ["tests/a.py"]) == ([], [])


def test_frontmatter_and_example():
    body = "---\ntitle: x\n---\nExample:\n```\n<!-- clutch:meta\nexample\n-->\n```\n"
    fs = MemoryFS({"docs/a.md": body})
    assert meta.check(config(), Path("/repo"), fs, ["docs/a.md"], "abc") == [("docs/a.md", "missing")]
    assert run(fs, ["docs/a.md"])[0] == ["docs/a.md"]
    text = fs.read_bytes(Path("/repo/docs/a.md")).decode()
    assert text.startswith("---\ntitle: x\n---\n<!-- clutch:meta\n")
    assert meta.parse(text, ".md")[1] == body


def test_generation_and_preservation():
    body = "from clutch import foo\n"
    files = ["tests/fixtures/a.py", "clutch/foo.py", "clutch/__init__.py"]
    fs = MemoryFS({files[0]: body})
    assert run(fs, files)[0] == [files[0]]
    path = Path("/repo") / files[0]
    text = fs.read_bytes(path).decode()
    fields, _, _ = meta.parse(text, ".py")
    assert fields["kind"] == "fixture" and fields["relates"] == ["clutch/foo.py"] and fields["owner"] == "clutch/foo.py"
    fs.files[path] = text.replace("# purpose: \n", "# purpose: useful\n").encode()
    assert run(fs, files)[0] == []
    assert b"purpose: useful" in fs.read_bytes(path)


def test_length_limit():
    names = [f"clutch/long_module_name_{i}.py" for i in range(20)]
    body = "".join(f"import clutch.long_module_name_{i}\n" for i in range(20))
    fs = MemoryFS({"tests/a.py": body})
    run(fs, ["tests/a.py", *names])
    line = next(line for line in fs.read_bytes(Path("/repo/tests/a.py")).decode().splitlines() if line.startswith("# relates:"))
    assert len(line) <= 160
    assert meta.parse(fs.read_bytes(Path("/repo/tests/a.py")).decode(), ".py")[0]["relates"] == sorted(names)[: len(line.removeprefix("# relates: [").removesuffix("]").split(", "))]


def test_links_filter_and_malformed():
    files = ["docs/a.md", "docs/b.md", "clutch/foo.py", "docs/ignored.txt"]
    fs = MemoryFS({"docs/a.md": "[b](b.md) clutch/foo.py::Thing [missing](no.md)\n", "docs/b.md": "<!-- clutch:meta\nbad\n-->\n"})
    assert run(fs, files) == (["docs/a.md"], ["docs/b.md"])
    fields, _, _ = meta.parse(fs.read_bytes(Path("/repo/docs/a.md")).decode(), ".md")
    assert fields["relates"] == ["clutch/foo.py", "docs/b.md"]
    assert fields["owner"] == "engine"
    assert meta.check(config(), Path("/repo"), fs, files, "abc", ["docs/b.md"]) == [("docs/b.md", "malformed")]


def test_invalid_python_does_not_generate_imports():
    fs = MemoryFS({"tests/a.py": "not valid python !\n"})
    assert run(fs, ["tests/a.py"]) == (["tests/a.py"], [])
    assert b"# relates: []" in fs.read_bytes(Path("/repo/tests/a.py"))
