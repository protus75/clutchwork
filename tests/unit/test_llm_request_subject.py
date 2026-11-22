# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that LLMRequest requires a non-empty string subject, that the driver validates subject against ticket and passes it on, and that no code still reads the old request ticket field
# relates: [clutch/driver.py, clutch/llm.py, clutch/redact.py, tests/fakes.py]
# owner: clutch/llm.py
# verified: 58c46bba
# hash: 41f2385f23249bd72dd161bb2cdbe3a117c1369d53d5909576442e0cf56a29df
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from clutch.driver import Driver, LlmStage, Spool
from clutch.llm import FakeLLM, LLMRequest
from clutch.redact import Redactor
from tests.fakes import FakeClock, FakeFileSystem, FakeJournal


class Reply(BaseModel):
    text: str


@pytest.mark.parametrize("subject", [None, "", 7])
def test_request_rejects_invalid_subject(subject):
    # A missing, empty, or non-string label must not construct a request.
    with pytest.raises(ValueError, match="subject must be a non-empty string"):
        LLMRequest("review", "prompt", "low", "low", subject, None)


@pytest.mark.asyncio
async def test_driver_subject_validation_and_propagation():
    clock = FakeClock()
    llm = FakeLLM(['{"text":"first"}', '{"text":"second"}'])
    redactor = Redactor({})
    driver = Driver(
        llm=llm,
        journal=FakeJournal(clock),
        redactor=redactor,
        spool=Spool(Path("/state"), redactor, FakeFileSystem()),
        log=SimpleNamespace(event=lambda *a, **kw: None),
        clock=clock,
        sleep=lambda _: None,
        severity={},
        retry_cap=0,
    )
    stage = LlmStage("review", Reply, [], lambda *_: "prompt")
    args = dict(attempt=1, workspace=Path("/repo"), tier="low", effort="low", stuck_budget=60, expected_budget=30, scope_fence=())
    # Invalid arguments must be rejected before any request reaches the provider.
    with pytest.raises(ValueError, match="subject must be a non-empty string when ticket is None"):
        await driver.run(stage, None, ticket=None, **args)
    with pytest.raises(ValueError, match="subject must be None when ticket is set"):
        await driver.run(stage, None, ticket="abc", subject="x", **args)
    assert llm.requests == []
    await driver.run(stage, None, ticket=None, subject="box-1", **args)
    await driver.run(stage, None, ticket="abc", **args)
    # Distinct labels rule out a constant, surface name, or swapped source.
    assert [r.subject for r in llm.requests] == ["box-1", "abc"]


def test_old_request_field_has_no_consumers():
    root = Path(__file__).resolve().parents[2]
    pattern = re.compile(r"\breq(?:uest)?\." + r"ticket\b")
    matches = []
    for directory in ("clutch", "tests"):
        for path in (root / directory).rglob("*.py"):
            lines = path.read_text().splitlines()
            if lines and lines[0] == "# clutch:meta":
                while lines and lines[0].startswith("#"):
                    lines.pop(0)
            matches.extend(f"{path}:{line}" for line in lines if pattern.search(line))
    assert matches == []
    for name in ("clutch/llm.py", "clutch/providers.py"):
        text = (root / name).read_text()
        assert "ticket=None, worktree" not in text
        assert not re.search(r'getattr\([^\n]*["\']ticket["\']', text)
    assert 'ticket="t-1"' not in (root / "tests/config_helpers.py").read_text()
