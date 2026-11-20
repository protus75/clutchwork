"""Committed conduct preflight without filesystem or subprocess access."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Committed conduct preflight without filesystem or subprocess access.
# relates: [clutch/git.py, clutch/hostfiles.py, clutch/providers.py]
# owner: engine
# verified: 0a308920
# hash: 096e5f0f8e04199aa501fc6c7ec17781b5e7cffc1a4b0dc11595020835d979e4

from pathlib import Path

import pytest

from clutch import hostfiles, providers
from clutch.git import GitError


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["current", "drifted", "missing", "absent"])
async def test_stale_core(state, monkeypatch):
    repo = Path("/repo")
    monkeypatch.setattr(providers, "routed_conduct_paths", lambda config, checkout: (checkout / "CLAUDE.md",))
    current = hostfiles.render(b"project rules\n").decode()
    files = {"HEAD:CLAUDE.md": {"current": current, "drifted": current.replace("## Engine conduct", "## Old conduct", 1), "missing": "project rules\n"}.get(state)}

    class FakeGit:
        async def _run(self, checkout, verb, ref):
            assert checkout == repo and verb == "show" and ref == "HEAD:CLAUDE.md"
            if files[ref] is None:
                raise GitError(["git", "show", ref], 1, "", "missing")
            return files[ref]

    messages = await hostfiles.stale_core(repo, object(), FakeGit())
    if state == "current":
        assert messages == []
    else:
        expected = "missing" if state == "absent" else state
        assert len(messages) == 1
        assert f"CLAUDE.md: clutch core is {expected}" in messages[0]
        assert "run `clutch host core`" in messages[0]
