# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for metafill.fill: drift-only blocks are refreshed without a model call and keep their descriptive lines, while empty-purpose and missing blocks go to the model and malformed blocks are rejected
# relates: [clutch/meta.py, clutch/metafill.py, tests/unit/test_meta_fill.py, tests/unit/test_meta_refresh.py]
# owner: engine
# verified: 9dc8c407
# hash: 6663f46745d6b96f7f52dbd2d02e9734f15015c0444c7990b266869eadc74ac2
import asyncio
import json
from pathlib import Path

from clutch import meta, metafill
from tests.unit.test_meta_fill import SPEC, entry
from tests.unit.test_meta_refresh import MemoryFS, config

ROOT = Path("/repo")


def block(purpose, owner="", relates=None):
    fields = dict(schema="clutch.meta/1.0", kind="plan", purpose=purpose, relates=relates or ["docs/stale.md"], owner=owner, verified="old", hash="old")
    return meta.compose(fields, "body\n", 0, ".md")[0]


def test_drift_only_preserves_descriptive_lines():
    path = "docs/drift.md"
    original = block("keep this")
    fs = MemoryFS({path: original})

    async def ask(paths, payload):
        raise AssertionError("drift must not reach the model")

    assert asyncio.run(metafill.fill(config(), ROOT, fs, [path], "abcdef123", SPEC, ask)) == ([path], [])
    result = fs.read_bytes(ROOT / path).decode()
    assert result == original.replace("verified: old", "verified: abcdef12").replace("hash: old", "hash: " + meta.digest("body\n"))


def test_mixed_targets_and_malformed():
    files = ["docs/drift.md", "docs/empty.md", "docs/missing.md", "docs/bad.md"]
    fs = MemoryFS({files[0]: block("keep"), files[1]: block(""), files[2]: "new body\n", files[3]: "<!-- clutch:meta\nbad\n-->\n"})
    calls = []

    async def ask(paths, payload):
        calls.append((paths, [item["path"] for item in json.loads(payload)]))
        return metafill.MetaReply(files={p: entry("written") for p in paths})

    written, rejected = asyncio.run(metafill.fill(config(), ROOT, fs, files, "abcdef123", SPEC, ask))
    assert calls == [(["docs/empty.md", "docs/missing.md"], ["docs/empty.md", "docs/missing.md"])]
    assert set(written) == set(files[:3])
    assert rejected == [("docs/bad.md", "malformed")]
    assert [meta.parse(fs.read_bytes(ROOT / p).decode(), ".md")[0]["purpose"] for p in files[:3]] == ["keep", "written", "written"]
