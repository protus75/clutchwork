# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verifies the release publishable check (token, dirty tree, publish off) matches publish's refusal and that journal_release writes the release signal
# relates: [clutch/journal.py, clutch/release.py, clutch/roadmap.py, clutch/runner.py, tests/fakes.py]
# owner: engine
# verified: 18f3cf87
# hash: d619ab34536a95d71757ebd214a562829ed843d442861c275d863b8388d5b72a
import asyncio
from datetime import datetime
from types import SimpleNamespace as NS

import pytest

from clutch import release, roadmap
from clutch.journal import EventType
from clutch.runner import Refusal
from tests.fakes import FakeJournal
from tests.git_fake import GitFake


def test_release_helpers(tmp_path):
    git = GitFake(status_porcelain=lambda *args: git.dirty)
    git.dirty = ""
    cfg = NS(release=NS(publish=True, pypi_token="TOKEN"))
    with pytest.raises(Refusal) as helper:
        asyncio.run(release.publishable(tmp_path, git, {}, cfg))
    with pytest.raises(Refusal) as full:
        asyncio.run(release.publish(tmp_path, git, None, None, {}, cfg))
    assert str(helper.value) == str(full.value) and git.calls == []
    git.dirty = " M x"
    with pytest.raises(Refusal, match="uncommitted tracked files"):
        asyncio.run(release.publishable(tmp_path, git, {"TOKEN": "secret"}, cfg))
    assert git.calls == [("status_porcelain", (tmp_path, "--untracked-files=no"), {})]
    git.dirty = ""
    cfg.release.publish = False
    assert asyncio.run(release.publishable(tmp_path, git, {}, cfg)) is None
    journal = FakeJournal()
    release.journal_release(journal, "0.4.0", "abc")
    assert [(e.type, e.body) for e in journal.events] == [(EventType.SIGNAL, {"signal": "release", "version": "0.4.0", "tag": "v0.4.0", "commit": "abc"})]
