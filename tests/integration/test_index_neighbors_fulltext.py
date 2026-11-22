"""Real extension neighbor searches."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks index neighbor search: full-text ranking, embedding search, and fallback to full-text when embedding fails
# relates: [clutch/box.py, clutch/index.py, tests/unit/test_index_build.py, tests/unit/test_index_sources.py]
# owner: engine
# verified: d32c32ad
# hash: 35289058408330e6e4ccbe2415367b382a3f134113783e32a616bc4ed7e89462

import json

import pytest

from clutch.box import Box
from clutch.index import default_creator, neighbors
from tests.unit.test_index_build import Exec, rig, run  # noqa: F401
from tests.unit.test_index_sources import put, record

pytestmark = pytest.mark.disk_io_skip


class Vectors(Exec):
    async def run(self, argv, **kwargs):
        text = kwargs["stdin_path"].read_text()
        self.calls.append((argv, kwargs))
        return 0, json.dumps([1, 0, 0] if "flaky test timeout in drain" in text else [0, 1, 0]), ""


@pytest.mark.asyncio
async def test_real_search_and_fallback(rig):
    rig.creator = default_creator
    box = Box(rig.config.state_dir / "box", rig.fs)
    flaky, _ = box.enqueue(message_class="suggestion", origin="test", summary="flaky test timeout in drain")
    other, _ = box.enqueue(message_class="suggestion", origin="test", summary="rename the doctor verb")
    put(
        rig,
        "docs/roadmap.md",
        "# Roadmap\n| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n|---|---|---|---|---|---|---|---|\n| 94 | `drain` | x | feature | P1 | - | - | drain timeout |\n",
    )
    put(rig, "tickets/decisions/d.md", record("d", "drain test"))
    findings = await run(rig)
    if any("unavailable:" in f for f in findings):
        pytest.skip("extensions unavailable")
    assert findings == []

    async def search(text):
        return await neighbors(rig.config, rig.root, text, fs=rig.fs, exec_=rig.exec, env={"X": "y"}, creator=rig.creator)

    result = await search("the drain test is flaky")
    assert (result.outcome, result.mode, result.findings) == ("found", "fulltext", ())
    assert result.hits[0].ref == flaky and result.hits[0].score > result.hits[1].score
    assert other not in [h.ref for h in result.hits]
    rig.config.index.embed = ["fake"]
    rig.exec = Vectors()
    findings = await run(rig)
    if any("unavailable:" in f for f in findings):
        pytest.skip("extensions unavailable")
    assert findings == []
    result = await search("flaky test timeout in drain")
    assert (result.outcome, result.mode) == ("found", "embedding")
    assert result.hits[0].ref == flaky and result.hits[0].score > result.hits[1].score
    rig.exec = Exec([(2, "", "")])
    result = await search("the drain test is flaky")
    assert (result.outcome, result.mode, result.findings) == ("found", "fulltext", ("embed_failed: exit 2",))
    assert result.hits[0].ref == flaky
