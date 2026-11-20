# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test gemini provider
# relates: [clutch/__init__.py, clutch/providers.py, clutch/seams.py, tests/integration/test_providers.py, tests/unit/test_gemini_adapter.py]
# owner: engine
# verified: 148a8874
# hash: b1fe88dea0ff1df7bf374db14cae0a0ea2089912569758855dcf4cf90ba84ec0
import asyncio
import json
from pathlib import Path

import pytest

import clutch
from clutch.providers import GeminiAdapter, ProviderCallError, ProviderLLM
from clutch.seams import LocalFileSystem
from tests.integration.test_providers import CONFIG, ENV, FakeExec, config, provider_session, req
from tests.unit.test_gemini_adapter import T02, T06_ERR, T27, adapter


def test_packaged_settings_files():
    a = adapter()
    for writes, name, expected in [
        (False, "gemini-readonly.json", {"tools": {"core": ["read_file", "glob", "grep_search", "list_directory"]}, "context": {"fileName": "AGENTS.md"}}),
        (True, "gemini-write.json", {"context": {"fileName": "AGENTS.md"}}),
    ]:
        path = Path(clutch.__file__).parent / name
        assert path.is_file() and Path(a.call_env(writes)["GEMINI_CLI_SYSTEM_SETTINGS_PATH"]) == path
        assert json.loads(path.read_text()) == expected


def test_calls_through_provider_llm(tmp_path):
    text = (
        CONFIG.replace("name: codex", "name: gemini")
        .replace("provider: codex", "provider: gemini")
        .replace("auth: CODEX_KEY", "auth: GEMINI_API_KEY")
        .replace("est_cost_per_call_usd: 1.5", "est_cost_per_call_usd: 0.5")
    )
    cfg = config(tmp_path, text)
    exec_ = FakeExec((0, T02, ""), (0, T02, ""), (0, T27, ""), (41, "", T06_ERR))
    llm = ProviderLLM(cfg, exec_=exec_, fs=LocalFileSystem(), env={**ENV, "GEMINI_API_KEY": "gemini-secret-key"}, cwd=tmp_path / "checkout", timeout=600, session=provider_session(cfg))

    async def run():
        result = await llm.call(req("review", tier="low", rendered="the prompt"))
        assert (result.text, result.model, result.usd) == ("PONG", "gemini-3.6-flash", 0.5)
        call = exec_.calls[-1]
        assert call["argv"][-2:] == ["--approval-mode", "default"]
        assert call["env"]["GEMINI_CLI_SYSTEM_SETTINGS_PATH"].endswith("gemini-readonly.json")
        assert call["env"]["GEMINI_API_KEY"] == "gemini-secret-key" and "CLAUDE_KEY" not in call["env"]
        assert call["stdin"] == "the prompt"
        await llm.call(req("implement", worktree=tmp_path / "worktree"))
        call = exec_.calls[-1]
        assert call["argv"][-2:] == ["--approval-mode", "yolo"]
        assert call["env"]["GEMINI_CLI_SYSTEM_SETTINGS_PATH"].endswith("gemini-write.json") and call["cwd"] == tmp_path / "worktree"
        with pytest.raises(ProviderCallError):
            await llm.call(req("review", tier="low"))
        with pytest.raises(ProviderCallError) as exc:
            await llm.call(req("review", tier="low"))
        assert exc.value.failure_class == "auth_error" and exc.value.paved_road == GeminiAdapter.LOGIN_ROAD

    asyncio.run(run())
