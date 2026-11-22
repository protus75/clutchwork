"""Real metadata/source and the composed in-memory filesystem boundary."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that LLM call evidence records stay on the in-memory filesystem with real engine and spec versions, and that the old spool capture path is gone.
# relates: [clutch/effects.py, clutch/evidence/store.py, clutch/llm.py, clutch/llmeffect.py, clutch/providers.py, clutch/redact.py, clutch/specs/__init__.py]
# owner: engine
# verified: d32c32ad
# hash: f5622b00c13cf5bfdf3d67af975b9044dbe4a40e5f5363768b92453b7dee7279

import asyncio
import importlib.metadata
import re
from pathlib import Path
from urllib.parse import quote

import pytest

from clutch import providers
from clutch.effects import Effects
from clutch.evidence.store import EvidenceStore
from clutch.llm import LLMRequest
from clutch.llmeffect import llm_call
from clutch.redact import Redactor
from clutch.specs import load_spec
from tests.integration.test_daemon_composition import CoreRig
from tests.integration.test_providers import ENV, provider_session

pytestmark = pytest.mark.disk_io_skip

ROOT = Path(__file__).resolve().parents[2]


def test_core_rig_records_stay_in_memory(tmp_path):
    rig = CoreRig(tmp_path)
    cfg = rig.checkout.config
    client = providers.ProviderLLM(cfg, exec_=rig.exec, fs=rig.fs, env=ENV, cwd=tmp_path, timeout=90, session=provider_session(cfg, rig.time, rig.time.sleep))
    key = "llm/memory/0/review/0/1"
    req = LLMRequest("review", "in-memory prompt", "medium", "high", "memory", None)
    result = asyncio.run(llm_call(Effects(client.session.journal), client, req, Redactor({}), ticket="memory", stem="memory", run_seq=0, attempt=0, call_seq=1))
    directory = cfg.state_dir / "evidence/calls" / quote(key, safe="")
    # Rules out real disk writers/readers, absent captures, and fake engine/spec versions.
    assert (result["text"], directory / "start.json" in rig.fs.files, directory / "end.json" in rig.fs.files, (cfg.state_dir / "evidence").exists()) == ("ok", True, True, False)
    store = EvidenceStore(cfg.state_dir, rig.fs, rig.fs.read_bytes, rig.fs.size, lambda text: text)
    start = store.read_record(key, "start")
    assert (start.engine.version, start.engine.spec_version) == (importlib.metadata.version("clutchwork"), load_spec((ROOT / "clutch/specs/review.md").read_text()).meta.version)


def test_old_capture_path_is_gone():
    # Rules out keeping a second capture writer or the obsolete harvest reader.
    forbidden = ["capture_sequence", "capture_dir", "_write_capture", "spools/providers", "spools/probe"]
    assert [(str(path), word) for path in (ROOT / "clutch").rglob("*.py") for word in forbidden if word in path.read_text()] == []
    assert [str(path) for path in (ROOT / "clutch").rglob("*.py") if re.search(r'"spools"\s*/\s*"(providers|probe)"', path.read_text())] == []
    rows = (ROOT / "docs/how-clutch-works.md").read_text().splitlines()
    assert any(row.startswith("| `evidence/` |") for row in rows)
    assert not any(row.startswith("| `spools/` |") for row in rows)
