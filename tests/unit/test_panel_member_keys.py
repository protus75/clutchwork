# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test panel member keys
# relates: [clutch/config.py, clutch/effects.py, clutch/evidence/store.py, clutch/llm.py, clutch/llmeffect.py, clutch/providers.py, clutch/redact.py]
# owner: engine
# verified: 9a610809
# hash: c4b94a2beafec788b74d9028af9e22776a27a9df9a0184a17795081886f1f5bb
import asyncio
from types import SimpleNamespace

import pytest

from clutch.llm import LLMRequest
from clutch.llmeffect import llm_key, member_index, scoped_seq
from clutch.providers import ProviderLLM
from tests.unit.test_evidence_envelope import ENV, Rig, stream
from tests.unit.test_route_kinds_filter import config
from tests.unit.test_route_panel_config import row


def test_key_shape_and_foreign_keys():
    key = llm_key("t", scoped_seq("m1", 3), "review", 1, 2)
    assert key == "llm/t/m1-3/review/1/2"
    prefix, stem, seq, surface, attempt, call = key.split("/")
    assert (prefix, stem, seq, surface, int(attempt), int(call)) == ("llm", "t", "m1-3", "review", 1, 2)
    assert member_index(key) == 1
    for other in ("llm/t/3/review/1/2", "llm/t/sup-3/review/1/2", "llm/t/m1-x/review/1/2", "llm/t/m1-3/review/1/2/extra", ""):
        assert member_index(other) is None
    assert member_index("llm/t/m" + "9" * 5000 + "-3/review/1/2") is None


@pytest.mark.asyncio
async def test_assignment_and_invalid_index():
    cfg = config(row(candidates="[{provider: codex, model: a}, {provider: claude, model: b}, {provider: codex, model: c}]"))
    calls = []

    class Thresh:
        def occupancy(self, name):
            return (0, 0, 1)

        def breakers(self):
            return {}

        async def run(self, route, **kwargs):
            calls.append([s.model for s in route])
            return SimpleNamespace(result=await kwargs["operation"](route[0]))

    client = object.__new__(ProviderLLM)
    client._config, client._timeout, client._exec, client._env = cfg, 1, None, {}
    client._adapters = {name: SimpleNamespace(within_budget=lambda req: True) for name in ("codex", "claude")}
    client.session = SimpleNamespace(thresh=Thresh(), clock=lambda: None, unavailable=lambda _: (False, None), sleep=None)
    captures = []

    async def invoke(req, served, *, consumer, capture):
        captures.append((served.model, capture.reason if capture else None))
        return served.model

    client._invoke = invoke
    req = LLMRequest("review", "prompt", "medium", "low", "t", None)

    async def effect(operation):
        return await operation()

    for scope in ("m1", "m0", None):
        key = llm_key("t", scoped_seq(scope, 1), "review", 1, 1)
        await client.admitted_call(req, ticket="t", call_key=key, effect=effect)
    assert calls == [["b", "a", "c"], ["a", "b", "c"], ["a", "b", "c"]]
    assert captures == [("b", "first"), ("a", "first"), ("a", "first")]
    cfg.routing[0].panel = None
    with pytest.raises(ValueError, match="index 1.*count 1"):
        await client.admitted_call(req, ticket="t", call_key="llm/t/m1-1/review/1/1", effect=effect)
    assert len(calls) == len(captures) == 3


def test_member_evidence(tmp_path, monkeypatch):
    from clutch.config import Panel
    from clutch.effects import Effects
    from clutch.evidence.store import EvidenceStore
    from clutch.llmeffect import llm_call
    from clutch.redact import Redactor
    from tests.fakes import FakeFileSystem

    rig = Rig(tmp_path, monkeypatch)
    rig.fs = FakeFileSystem()
    rig.exec.fs = rig.fs
    for adapter in rig.client._adapters.values():
        adapter._fs = rig.fs
    rig.store = EvidenceStore(rig.cfg.state_dir, rig.fs, rig.fs.read_bytes, rig.fs.size, lambda value: value)
    rig.cfg.routing[0].panel = Panel(size=2, combine="findings-union")
    rig.exec.out = stream(codex=True)
    key = "llm/ticket/m1-1/review/2/4"
    asyncio.run(llm_call(Effects(rig.journal), rig.client, rig.request(), Redactor.from_config(rig.cfg, ENV), ticket="ticket", stem="ticket", run_seq=scoped_seq("m1", 1), attempt=2, call_seq=4))
    start = rig.store.read_record(key, "start")
    assert (start.schema_, start.id, start.run_seq) == ("clutch.evidence.call/1.0", key, "m1-1")
    assert start.route.reason == "first"
