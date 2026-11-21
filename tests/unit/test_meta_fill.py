# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Metadata fill validation, batching and preservation
# relates: [clutch/artifacts.py, clutch/meta.py, clutch/metafill.py, clutch/specs/__init__.py, tests/unit/test_meta_refresh.py]
# owner: engine
# verified: 75d75946
# hash: 627ab99e9060a025108eedd7dcb7f053e5329a7b4a70c190e6878557e338bd72
import asyncio
import json
from pathlib import Path

import pytest

from clutch import meta, metafill
from clutch.specs import load_spec, render
from tests.unit.test_meta_refresh import MemoryFS, config

SPEC = load_spec("""---
llm_surface: meta
tier: medium
effort: medium
version: "1.0"
---
## Role
Describe files.
## Task
Return descriptions.
## Inputs
<<clutch-data:begin files>>
{{files}}
<<clutch-data:end files>>
<<clutch-data:begin retry_findings>>
{{retry_findings}}
<<clutch-data:end retry_findings>>
## Output format
Return text.
## On-failure
Stop.
""")
ROOT = Path("/repo")


def entry(purpose="A useful purpose", relates=None, owner="engine"):
    return metafill.MetaEntry(purpose=purpose, relates=relates or [], owner=owner)


def run(fs, tracked, ask):
    return asyncio.run(metafill.fill(config(), ROOT, fs, tracked, "abcdef123456", SPEC, ask))


def test_valid_entry_stamps_and_checks():
    fs = MemoryFS({"docs/a.md": "body\n"})

    async def ask(paths, payload):
        assert json.loads(payload)[0]["content"] == "body\n"
        return metafill.MetaReply(files={paths[0]: entry()})

    assert run(fs, ["docs/a.md"], ask) == (["docs/a.md"], [])
    fields, body, _ = meta.parse(fs.read_bytes(ROOT / "docs/a.md").decode(), ".md")
    assert (fields["purpose"], fields["verified"], fields["hash"]) == ("A useful purpose", "abcdef12", meta.digest("body\n"))
    assert body == "body\n"
    assert meta.check(config(), ROOT, fs, ["docs/a.md"], "abcdef123456") == []


@pytest.mark.parametrize("bad", [entry("bad-->text"), entry("bad\ntext"), entry(relates=["missing.py"]), entry(owner="x\n-->\nanything")])
@pytest.mark.parametrize("suffix", ["md", "py"])
def test_bad_entry_does_not_write_with_valid_sibling(bad, suffix):
    first, sibling = f"tests/a.{suffix}", f"tests/b.{suffix}"
    fs = MemoryFS({first: "original\n", sibling: "other\n"})

    async def ask(paths, payload):
        return metafill.MetaReply(files={first: bad, sibling: entry()})

    written, rejected = run(fs, [first, sibling], ask)
    assert fs.read_bytes(ROOT / first) == b"original\n"
    assert written == [sibling]
    assert rejected[0][0] == first
    assert meta.parse(fs.read_bytes(ROOT / sibling).decode(), "." + suffix)[0]["purpose"] == "A useful purpose"


def test_preserve_generated_and_existing_owner():
    fs = MemoryFS({"docs/a.md": "[b](b.md)\n", "docs/b.md": "other\n"})
    meta.refresh(config(), ROOT, fs, ["docs/a.md", "docs/b.md"], "12345678")

    async def ask(paths, payload):
        return metafill.MetaReply(files={p: entry(relates=["docs/a.md"], owner="another") for p in paths})

    run(fs, ["docs/a.md", "docs/b.md"], ask)
    fields = meta.parse(fs.read_bytes(ROOT / "docs/a.md").decode(), ".md")[0]
    assert fields["relates"] == ["docs/b.md"]
    assert fields["owner"] == "docs/b.md"


def test_trim_and_blank_owner_stable():
    names = [f"clutch/long_module_name_{i}.py" for i in range(20)]
    fs = MemoryFS({"tests/a.py": "value = 4\n", "tests/b.py": "".join(f"import clutch.long_module_name_{i}\n" for i in range(20))})
    tracked = ["tests/a.py", "tests/b.py", *names]

    async def ask(paths, payload):
        return metafill.MetaReply(files={p: entry(relates=sorted(names), owner="  ") for p in paths})

    run(fs, tracked, ask)
    a = meta.parse(fs.read_bytes(ROOT / "tests/a.py").decode(), ".py")[0]
    b = meta.parse(fs.read_bytes(ROOT / "tests/b.py").decode(), ".py")[0]
    assert a["relates"] == b["relates"] and len(a["relates"]) < len(names)
    assert a["owner"] == "engine"
    assert meta.refresh(config(), ROOT, fs, tracked, "abcdef123456") == ([], [])


def test_batches_and_review_paths():
    paths = [f"docs/{i:02}.md" for i in range(45)]
    fs = MemoryFS({p: "body\n" for p in paths})
    calls = []

    async def ask(batch, payload):
        calls.append(len(batch))
        return metafill.MetaReply(files={p: entry() for p in batch})

    assert len(run(fs, paths, ask)[0]) == 45
    assert calls == [20, 20, 5]
    report = metafill.review_reply(["docs/asked.md"], metafill.MetaReply(files={"docs/added.md": entry()}))
    assert report.verdict == "fail"
    assert {f.message for f in report.findings} == {"missing path: docs/asked.md", "extra path: docs/added.md"}
    assert metafill.review_reply(["docs/asked.md"], metafill.MetaReply(files={"docs/asked.md": entry()})).verdict == "pass"


def test_adapter_renders_retry_findings():
    class Driver:
        async def run(self, stage, *args, **kwargs):
            from types import SimpleNamespace

            from clutch.artifacts import Finding

            prompt = stage.render(None, [Finding(code="bad", message="retry this", paved_road="fix it")])
            assert "retry this" in prompt
            assert "the payload" in prompt
            return SimpleNamespace(outcome="gate_failed", artifact=None)

    ask = metafill.make_ask(Driver(), SPEC, ROOT, 7)
    assert asyncio.run(ask(["docs/a.md"], "the payload")) is None
    assert ask.outcome == "gate_failed"


def test_rejected_existing_block_is_unchanged():
    fs = MemoryFS({"docs/a.md": "body\n", "docs/b.md": "other\n"})
    paths = ["docs/a.md", "docs/b.md"]
    meta.refresh(config(), ROOT, fs, paths, "abcdef123")
    before = fs.read_bytes(ROOT / paths[0])

    async def ask(batch, payload):
        return metafill.MetaReply(files={paths[0]: entry("bad-->value"), paths[1]: entry()})

    written, rejected = run(fs, paths, ask)
    assert written == [paths[1]]
    assert rejected == [(paths[0], "invalid purpose")]
    assert fs.read_bytes(ROOT / paths[0]) == before
