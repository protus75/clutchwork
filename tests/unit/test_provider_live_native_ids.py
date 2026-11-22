# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that a provider call rewrites its evidence start record with the first session id as soon as the stream reports it, before the call returns, and leaves native_ids null when no id appears
# relates: [tests/unit/test_evidence_envelope.py]
# owner: tests/unit/test_evidence_envelope.py
# verified: 19880b1d
# hash: cd58f96d1515014595c5392e00052fc7a34c22b76ba7aa2653152c72ea5d557b
import asyncio
import json

from tests.unit.test_evidence_envelope import Rig, stream


def test_first_id_is_visible_before_return(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    original = rig.exec.run
    seen = []

    async def run(argv, **kwargs):
        callback = kwargs.get("on_stdout_line")
        if callback and argv[0] != "git":

            def line(value):
                callback(value)
                seen.append(rig.record("start").native_ids)

            kwargs["on_stdout_line"] = line
        return await original(argv, **kwargs)

    rig.exec.run = run
    rig.exec.out = 'not json\n{"session_id":"s1"}\n{"session_id":"s2"}\n' + stream().splitlines()[-1] + "\n"
    asyncio.run(rig.call())
    assert seen[0] is None
    assert seen[1].session_id == "s1"
    assert seen[2].session_id == "s1"


def test_no_id_stays_null(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    rig.exec.out = json.dumps({"type": "result", "subtype": "success", "result": "done", "total_cost_usd": 0.1}) + "\n"
    asyncio.run(rig.call())
    assert rig.record("start").native_ids is None
