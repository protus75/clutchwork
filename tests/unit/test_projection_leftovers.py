from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from clutch import observe, tickets
from clutch.driver import Driver
from clutch.enginelog import engine_log_path


def test_driver_shares_redactor(monkeypatch, tmp_path):
    monkeypatch.setattr("clutch.driver.merge_severity", lambda config: {})
    config = SimpleNamespace(state_dir=tmp_path, providers=[], release=SimpleNamespace(pypi_token=""), caps=SimpleNamespace(retry=3))
    driver = Driver.from_config(config, llm=Mock(), env={}, clock=Mock(), sleep=Mock(), journal=SimpleNamespace(read=lambda: []))
    assert driver.log._redactor is driver.spool._redactor


def test_log_path_and_watch_glob():
    assert engine_log_path(Path("s")) == Path("s/engine.log")
    assert observe.WATCH_STATE_GLOB == "{journal/*.jsonl,queue.json,engine.log,box/*.json}"


def test_ticket_artifact_paths():
    for name, expected in [
        (tickets.RUN_FILE, "run.md"),
        (tickets.REVIEW_FILE, "review.md"),
        (tickets.CHECKS_FILE, "checks.json"),
        (tickets.DIAGNOSIS_FILE, "diagnosis.json"),
        (tickets.REWORK_FILE, "rework.md"),
    ]:
        assert tickets.artifact_path("alpha", name) == f"tickets/alpha/{expected}"
    assert tickets.harvest_path("alpha", 7) == "tickets/alpha/attempts/7/harvest.json"
