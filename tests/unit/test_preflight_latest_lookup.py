# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test preflight latest lookup
# relates: [clutch/seams.py, tests/unit/test_preflight_parallel.py]
# owner: engine
# verified: 9a610809
# hash: 50406442f06485b5118219efeba243c36f7cb8c9ccbea25996de48a63de71be6
import json

import pytest

from clutch.seams import ExecutableNotFound
from tests.unit.test_preflight_parallel import ProbeExec, make_client


class LatestExec(ProbeExec):
    def __init__(self, error=None, latest="1.0.0"):
        super().__init__(refused={"one"})
        self.error = error
        self.latest = latest

    async def run(self, argv, **kwargs):
        if argv[:2] == ["pnpm", "view"]:
            if self.error:
                self.calls.append(list(argv))
                raise self.error
            self.calls.append(list(argv))
            return 0, self.latest, ""
        if argv[1:] == ["--version"]:
            self.calls.append(list(argv))
            return 0, "1.0.0", ""
        self.calls.append(list(argv))
        model = argv[argv.index("--model" if argv[0] == "claude" else "-m") + 1]
        if model == "one":
            return 1, "", "refused one"
        event = {"type": "result", "subtype": "success", "result": "ok", "total_cost_usd": 1} if argv[0] == "claude" else {"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}}
        return 0, json.dumps(event) + ("\n" + json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}}) if argv[0] == "codex" else ""), ""


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [TimeoutError(), ExecutableNotFound("pnpm")])
async def test_lookup_failure_keeps_versions_and_probes(error):
    baseline_exec = LatestExec()
    baseline = await make_client(baseline_exec).preflight()
    exec_ = LatestExec(error=error)
    client = make_client(exec_)

    problems = await client.preflight()

    assert problems == baseline
    assert len(problems) == 1 and "model 'one'" in problems[0]
    assert client.preflight_notices == []
    assert [adapter.cli_version for adapter in client._adapters.values()] == ["1.0.0", "1.0.0"]
    assert [(call[0], call[call.index("--model" if call[0] == "claude" else "-m") + 1]) for call in exec_.calls[4:]] == [("codex", "one"), ("claude", "two"), ("codex", "three")]


@pytest.mark.asyncio
async def test_empty_lookup_is_unreadable():
    client = make_client(LatestExec(latest=""))
    await client.preflight()
    assert len(client.preflight_notices) == 2
    assert all("(unreadable)" in notice for notice in client.preflight_notices)
