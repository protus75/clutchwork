"""Resource usage survives successful and exceptional provider calls."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Resource usage survives successful and exceptional provider calls.
# relates: [clutch/evidence/schema.py, clutch/git.py, clutch/providers.py, tests/unit/test_evidence_envelope.py]
# owner: engine
# verified: 0a308920
# hash: 2abbdb350216e18756fd3989cd38212e4bd4cb490a74d6cd03fc2b3306cdc9c6

import asyncio

import pytest

from clutch.evidence.schema import Rusage
from clutch.git import Git
from clutch.providers import CallCapture
from tests.unit.test_evidence_envelope import ENV, KEY, Rig

USAGE = {"user_s": 1.5, "sys_s": 0.25, "max_rss_kb": 20480}


def invoke(rig, *, capture=True):
    adapter = rig.client._adapters["claude"]
    evidence = CallCapture(KEY, "ticket", ("claude",), "first", Git(rig.exec, env=ENV, timeout=10, commit_lock=None), rig.clock) if capture else None
    return asyncio.run(adapter.invoke(rig.request(), "requested-claude", capture=evidence))


def install_usage(rig, *, report, timeout=False):
    original = rig.exec.run

    async def run(argv, **kwargs):
        if argv[0] != "git":
            if report:
                kwargs["on_rusage"](Rusage(**USAGE))
            if timeout:
                raise TimeoutError()
        return await original(argv, **kwargs)

    rig.exec.run = run


def test_reported_rusage_is_recorded(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    install_usage(rig, report=True)
    invoke(rig)
    # Rules out discarding or swapping the seam's distinct figures.
    assert rig.record().rusage.model_dump() == USAGE


def test_missing_report_remains_null(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    install_usage(rig, report=False)
    invoke(rig)
    # Rules out fabricated zero usage when the seam never reports.
    assert rig.record().rusage is None


def test_timeout_keeps_reported_rusage(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    install_usage(rig, report=True, timeout=True)
    with pytest.raises(TimeoutError):
        invoke(rig)
    end = rig.record()
    # Rules out losing the report on unwind or misclassifying the timeout.
    assert end.exit.status == "timeout"
    assert end.rusage.model_dump() == USAGE


def test_no_capture_omits_keyword(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    invoke(rig, capture=False)
    # Rules out passing a null callback to older fixed-signature executors.
    assert "on_rusage" not in rig.exec.calls[-1][1]
