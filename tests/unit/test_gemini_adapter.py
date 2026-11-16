import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import clutch
from clutch import providers
from clutch.config import Limits, ModelsByTier, Provider, load_config_text
from clutch.providers import CliStatus, GeminiAdapter, ModelListing, ProviderSetupError

T17 = '{"type":"init","timestamp":"2026-11-16T03:07:46.581Z","session_id":"cd770438-4260-47b8-8c0d-2085fc1b7055","model":"gemini-2.5-flash"}\n{"type":"message","timestamp":"2026-11-16T03:07:46.582Z","role":"user","content":"Use your own tools directly (do not delegate to a subagent) to do two things: (1) create a file named out.txt in the current directory containing the word WRITTEN; (2) run the shell command: echo SHELL > shell.txt . Then say DONE and list which steps succeeded.\\n"}\n{"type":"tool_use","timestamp":"2026-11-16T03:07:52.272Z","tool_name":"update_topic","tool_id":"update_topic__call_4935615467816418684","parameters":{"title":"File Creation and Shell Command Execution","strategic_intent":"Creating out.txt and executing shell command to write shell.txt","summary":"I will create out.txt directly with the text \'WRITTEN\' and execute the shell command to output \'SHELL\' into shell.txt."}}\n{"type":"tool_use","timestamp":"2026-11-16T03:07:52.321Z","tool_name":"write_file","tool_id":"write_file__call_4935615467816417309","parameters":{"file_path":"out.txt","content":"WRITTEN"}}\n{"type":"tool_use","timestamp":"2026-11-16T03:07:52.523Z","tool_name":"run_shell_command","tool_id":"run_shell_command__call_4935615467816415934","parameters":{"command":"echo SHELL > shell.txt","description":"Executes shell command to write SHELL into shell.txt"}}\n{"type":"tool_result","timestamp":"2026-11-16T03:07:52.593Z","tool_id":"update_topic__call_4935615467816418684","status":"success","output":"## 📂 Topic: **File Creation and Shell Command Execution**\\n\\n**Summary:**\\nI will create out.txt directly with the text \'WRITTEN\' and execute the shell command to output \'SHELL\' into shell.txt.\\n\\n> [!STRATEGY]\\n> **Intent:** Creating out.txt and executing shell command to write shell.txt"}\n{"type":"tool_result","timestamp":"2026-11-16T03:07:52.593Z","tool_id":"write_file__call_4935615467816417309","status":"success"}\n{"type":"tool_result","timestamp":"2026-11-16T03:07:52.593Z","tool_id":"run_shell_command__call_4935615467816415934","status":"success","output":""}\n{"type":"message","timestamp":"2026-11-16T03:07:53.773Z","role":"assistant","content":"DONE\\n\\n","delta":true}\n{"type":"message","timestamp":"2026-11-16T03:07:53.901Z","role":"assistant","content":"Steps succeeded:\\n1. Created `out.txt` containing `WRITTEN`.\\n2. Ran `echo SHELL > shell.","delta":true}\n{"type":"message","timestamp":"2026-11-16T03:07:53.972Z","role":"assistant","content":"txt` to create `shell.txt`.","delta":true}\n{"type":"result","timestamp":"2026-11-16T03:07:53.982Z","status":"success","stats":{"total_tokens":23016,"input_tokens":21982,"output_tokens":186,"cached":8344,"input":13638,"duration_ms":7401,"tool_calls":3,"models":{"gemini-3.6-flash":{"total_tokens":23016,"input_tokens":21982,"output_tokens":186,"cached":8344,"input":13638}}}}\n'  # noqa: E501
T02 = '{"type":"init","timestamp":"2026-11-16T03:03:19.550Z","session_id":"be37ee64-e05b-41dd-aa30-34eb42623e6f","model":"gemini-2.5-flash"}\n{"type":"message","timestamp":"2026-11-16T03:03:19.550Z","role":"user","content":"Reply with the single word PONG."}\n{"type":"message","timestamp":"2026-11-16T03:03:21.490Z","role":"assistant","content":"PONG","delta":true}\n{"type":"result","timestamp":"2026-11-16T03:03:21.517Z","status":"success","stats":{"total_tokens":7624,"input_tokens":7318,"output_tokens":2,"cached":0,"input":7318,"duration_ms":1968,"tool_calls":0,"models":{"gemini-3.6-flash":{"total_tokens":7624,"input_tokens":7318,"output_tokens":2,"cached":0,"input":7318}}}}\n'  # noqa: E501
T27 = '{"type":"init","timestamp":"2026-11-16T03:12:36.846Z","session_id":"5a08bd51-6778-45ac-b919-c9579a240dac","model":"gemini-3.1-flash-image-preview"}\n{"type":"message","timestamp":"2026-11-16T03:12:36.847Z","role":"user","content":"Generate an image of a red circle."}\n{"type":"error","timestamp":"2026-11-16T03:12:44.735Z","severity":"error","message":"Invalid stream: The model returned an empty response or malformed tool call."}\n{"type":"result","timestamp":"2026-11-16T03:12:44.735Z","status":"error","stats":{"total_tokens":10056,"input_tokens":8650,"output_tokens":1406,"cached":0,"input":8650,"duration_ms":7889,"tool_calls":0,"models":{"gemini-3.1-flash-image-preview":{"total_tokens":10056,"input_tokens":8650,"output_tokens":1406,"cached":0,"input":8650}}}}\n'  # noqa: E501
T04 = '{"type":"init","timestamp":"2026-11-16T03:04:19.834Z","session_id":"e2be0dfb-bff3-4c91-975c-11a89e4fb821","model":"gemini-nonexistent-a0"}\n{"type":"message","timestamp":"2026-11-16T03:04:19.835Z","role":"user","content":"Reply with the single word PONG."}\n{"type":"result","timestamp":"2026-11-16T03:04:20.024Z","status":"error","error":{"type":"unknown","message":"[API Error: An unknown error occurred.]"},"stats":{"total_tokens":0,"input_tokens":0,"output_tokens":0,"cached":0,"input":0,"duration_ms":0,"tool_calls":0,"models":{"gemini-nonexistent-a0":{"total_tokens":0,"input_tokens":0,"output_tokens":0,"cached":0,"input":0}}}}\n'  # noqa: E501

T06_ERR = "Please set an Auth method in your <scratch>/home/.gemini/settings.json or specify one of the following environment variables before running: GEMINI_API_KEY, GOOGLE_GENAI_USE_VERTEXAI, GOOGLE_GENAI_USE_GCA"  # noqa: E501
T07_ERR = 'Error when talking to Gemini API Full report available at: /tmp/gemini-client-error-Turn.run-sendMessageStream-2026-11-16T03-04-48-971Z.json _ApiError: {"error":{"message":"{\\n  \\"error\\": {\\n    \\"code\\": 400,\\n    \\"message\\": \\"API key not valid. Please pass a valid API key.\\",\\n    \\"status\\": \\"INVALID_ARGUMENT\\",\\n    \\"details\\": [\\n      {\\n        \\"@type\\": \\"type.googleapis.com/google.rpc.ErrorInfo\\",\\n        \\"reason\\": \\"API_KEY_INVALID\\",\\n        \\"domain\\": \\"googleapis.com\\",\\n        \\"metadata\\": {\\n          \\"service\\": \\"generativelanguage.googleapis.com\\"\\n        }\\n      },\\n      {\\n        \\"@type\\": \\"type.googleapis.com/google.rpc.LocalizedMessage\\",\\n        \\"locale\\": \\"en-US\\",\\n        \\"message\\": \\"API key not valid. Please pass a valid API key.\\"\\n      }\\n    ]\\n  }\\n}\\n","code":400,"status":"Bad Request"}}\n  status: 400\n}'  # noqa: E501
T34_ERR = "Error when talking to Gemini API Full report available at: /tmp/gemini-client-error-Turn.run-sendMessageStream-2026-11-16T03-16-38-460Z.json ModelNotFoundError: This model models/gemini-2.5-pro is no longer available to new users. Please update your code to use models/gemini-3.1-pro-preview for the latest features and improvements. We recommend you to use the Interactions API (https://aistudio.google.com/docs/get-started).\n  code: 404\n}"  # noqa: E501


def provider(name="gemini", auth="GEMINI_API_KEY", estimate=0.5, base_url=None):
    return Provider(
        name=name,
        kind="cli",
        package="pkg",
        auth=auth,
        base_url=base_url,
        models_by_tier=ModelsByTier(low="a", medium="b", high="c", max="d"),
        limits=Limits(concurrency=1, est_cost_per_call_usd=estimate),
    )


def adapter(p=None):
    p = p or provider()
    other = provider("claude", "CLAUDE_KEY")
    config = SimpleNamespace(providers=[p, other], release=SimpleNamespace(pypi_token="UV_PUBLISH_TOKEN"))
    return GeminiAdapter(
        p,
        config=config,
        exec_=Mock(),
        fs=Mock(),
        redactor=SimpleNamespace(scrub=lambda x: x),
        env={"PATH": "/bin", "GEMINI_API_KEY": "g", "CLAUDE_KEY": "c"},
        cwd=Path("/repo"),
        capture_dir=Path("/capture"),
        timeout=120,
    )


def test_argv_grants():
    a = adapter()
    expected = ["gemini", "--skip-trust", "-m", "gemini-3.1-flash-lite", "-o", "stream-json", "--approval-mode", "default"]
    assert a.argv("gemini-3.1-flash-lite", "high", False) == expected
    expected[-1] = "yolo"
    assert a.argv("gemini-3.1-flash-lite", "high", True) == expected


def test_call_env_selects_the_grant_file():
    a = adapter()
    for writes, name in [(False, "gemini-readonly.json"), (True, "gemini-write.json")]:
        env = a.call_env(writes)
        path = Path(env["GEMINI_CLI_SYSTEM_SETTINGS_PATH"])
        assert path.is_absolute() and path == Path(clutch.__file__).parent / name
        assert env["GEMINI_API_KEY"] == "g" and "CLAUDE_KEY" not in env
        assert env["PATH"].startswith("/repo/node_modules/.bin")


def test_parse_success():
    a = adapter()
    p = a.parse(T17)
    assert p.text == "DONE\n\nSteps succeeded:\n1. Created `out.txt` containing `WRITTEN`.\n2. Ran `echo SHELL > shell.txt` to create `shell.txt`."
    assert (p.input_tokens, p.output_tokens, p.usd, p.model) == (21982, 186, None, "gemini-3.6-flash")
    p = a.parse(T02)
    assert (p.text, p.model) == ("PONG", "gemini-3.6-flash")
    p = a.parse(json.dumps({"type": "result", "status": "success", "stats": {"models": {"a": {}, "b": {}}}}))
    assert p.model is None


def test_parse_failures():
    for stream, message in [(T27, "Invalid stream"), (T04, r"\[API Error: An unknown error occurred.\]"), ("", "no terminal result event")]:
        with pytest.raises(ValueError, match=message):
            adapter().parse(stream)


def test_failure_classes():
    a = adapter()
    cases = [
        (41, T06_ERR, "auth_error"),
        (144, T07_ERR, "auth_error"),
        (1, T34_ERR, "model_error"),
        (1, "You have exhausted your daily quota on this model. (Status: RESOURCE_EXHAUSTED)", "quota_exhausted"),
        (
            1,
            "[API Error: Resource has been exhausted (e.g. check quota). (Status: RESOURCE_EXHAUSTED)] "
            "Please wait and try again later. To increase your limits, request a quota increase through AI Studio, or switch to another /auth method",
            "rate_limited",
        ),
    ]
    for rc, stderr, kind in cases:
        result = a.classify_failure("nonzero exit", rc=rc, stderr_tail=stderr)
        assert result.failure_class == kind
        if kind == "auth_error":
            assert result.paved_road == GeminiAdapter.LOGIN_ROAD


def test_registry_listing_and_conduct():
    assert providers.ADAPTERS["gemini"] is GeminiAdapter
    assert (GeminiAdapter.PACKAGE, GeminiAdapter.binary, GeminiAdapter.reports_cost) == ("@google/gemini-cli", "gemini", False)
    listing = asyncio.run(GeminiAdapter.list_models(exec_=Mock(run=Mock(side_effect=AssertionError)), env={}, cwd=Path("/repo")))
    assert listing.models == {} and len(listing.problems) == 1
    assert "host-gemini.md" in listing.problems[0] and "clutch probe gemini" in listing.problems[0]
    status = CliStatus("gemini", "@google/gemini-cli", "gemini", "system", "0.49.0")
    text = providers.suggest_config([status], {"gemini": listing})
    assert "    package: '@google/gemini-cli'\n    auth: GEMINI_API_KEY\n" in text
    assert text.count("OPERATOR-SETS-THIS") == 4 and "est_cost_per_call_usd: 0.25" in text
    assert load_config_text(text, path=Path("/repo/config.yaml"), cwd=Path("/repo")).providers[0].auth == "GEMINI_API_KEY"
    claude = CliStatus("claude", "@anthropic-ai/claude-code", "claude", "system", "1")
    assert "    auth:" not in providers.suggest_config([claude], {"claude": ModelListing({}, ())})
    p = provider()
    route = SimpleNamespace(tier="low", surface="review", candidates=[SimpleNamespace(provider="gemini", model=None)])
    assert providers.routed_conduct_paths(SimpleNamespace(providers=[p], routing=[route]), Path("/checkout")) == (Path("/checkout/AGENTS.md"),)
    for p in (provider(estimate=None), provider(base_url="http://localhost")):
        with pytest.raises(ProviderSetupError):
            adapter(p)
