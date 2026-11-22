"""Committed conduct preflight without filesystem or subprocess access."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the committed conduct preflight that reports a clutch core block that is current, drifted or missing, without filesystem or subprocess access
# relates: [clutch/git.py, clutch/hostfiles.py, clutch/providers.py]
# owner: engine
# verified: c015c627
# hash: d9fb6b430db00afe1fc87225ff70bd44007e11c1103b933e3b500aa37f3ae87e

from pathlib import Path

import pytest

from clutch import hostfiles, providers
from clutch.git import GitError
from tests.git_fake import GitFake


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["current", "drifted", "missing", "absent"])
async def test_stale_core(state, monkeypatch):
    repo = Path("/repo")
    monkeypatch.setattr(providers, "routed_conduct_paths", lambda config, checkout: (checkout / "CLAUDE.md",))
    current = hostfiles.render(b"project rules\n").decode()
    files = {"HEAD:CLAUDE.md": {"current": current, "drifted": current.replace("## Engine conduct", "## Old conduct", 1), "missing": "project rules\n"}.get(state)}

    async def run(checkout, verb, ref):
        assert checkout == repo and verb == "show" and ref == "HEAD:CLAUDE.md"
        if files[ref] is None:
            raise GitError(["git", "show", ref], 1, "", "missing")
        return files[ref]

    messages = await hostfiles.stale_core(repo, object(), GitFake(_run=run))
    if state == "current":
        assert messages == []
    else:
        expected = "missing" if state == "absent" else state
        assert len(messages) == 1
        assert f"CLAUDE.md: clutch core is {expected}" in messages[0]
        assert "run `clutch host core`" in messages[0]
