# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Check that provider call evidence captures survive a new process and are keyed by stem and run
# relates: [clutch/effects.py, clutch/evidence/store.py, clutch/llmeffect.py, clutch/redact.py, clutch/seams.py, tests/integration/test_providers.py]
# owner: clutch/llmeffect.py
# verified: 38957300
# hash: 5826601a3e0d2000d9ecb41b5271c69cbf5642b9bad10838514799d64ffc5121
import asyncio
from dataclasses import replace

import pytest

from clutch.effects import Effects
from clutch.evidence.store import EvidenceStore
from clutch.llmeffect import llm_call
from clutch.redact import Redactor
from clutch.seams import LocalFileSystem
from tests.config_helpers import ENV, FakeExec, claude_ok, config, llm, req

pytestmark = pytest.mark.disk_io_skip


def invoke(client, cfg, request, sequence):
    return asyncio.run(llm_call(Effects(client.session.journal), client, request, Redactor.from_config(cfg, ENV), ticket=request.ticket, stem=request.ticket, run_seq=sequence, attempt=0, call_seq=1))


def stdout(cfg, key):
    fs = LocalFileSystem()
    store = EvidenceStore(cfg.state_dir, fs, fs.read_bytes, fs.size, lambda text: text)
    return store.get_blob(store.read_record(key, "end").raw.stdout).decode()


def test_capture_survives_new_process(tmp_path):
    cfg = config(tmp_path)
    first = llm(cfg, FakeExec((0, claude_ok("first run"), "")), tmp_path)
    second = llm(cfg, FakeExec((0, claude_ok("second run"), "")), tmp_path)
    invoke(first, cfg, req("review"), 0)
    invoke(second, cfg, req("review"), 1)
    assert "first run" in stdout(cfg, "llm/t-1/0/review/0/1")
    assert "second run" in stdout(cfg, "llm/t-1/1/review/0/1")
    assert len(list((cfg.state_dir / "evidence/calls").iterdir())) == 2


def test_capture_numbers_are_per_stem(tmp_path):
    cfg = config(tmp_path)
    client = llm(cfg, FakeExec((0, claude_ok("first"), ""), (0, claude_ok("second"), "")), tmp_path)
    invoke(client, cfg, req("review"), 0)
    invoke(client, cfg, replace(req("review"), ticket="t-2"), 0)
    assert "first" in stdout(cfg, "llm/t-1/0/review/0/1")
    assert "second" in stdout(cfg, "llm/t-2/0/review/0/1")
