# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test effects recorded
# relates: [clutch/effects.py, clutch/journal.py]
# owner: engine
# verified: 0a308920
# hash: 67b7a4666b04df37d1cfd3e2f5414571d3d7703b8f43ff836dba8fe6d6fda86b
from datetime import UTC, datetime

import pytest

from clutch.effects import Effects
from clutch.journal import EventType, Journal


@pytest.mark.asyncio
async def test_recorded_and_replay(tmp_path):
    journal = Journal(tmp_path, lambda: datetime(2026, 1, 1, tzinfo=UTC))
    journal.append(EventType.EFFECT_INTENT, {}, key="shared", ticket="a")
    journal.append(EventType.EFFECT_COMPLETION, {"result": "first"}, key="shared", ticket="a")
    journal.append(EventType.EFFECT_COMPLETION, {"result": "second"}, key="shared", ticket="foreign")
    journal.append(EventType.EFFECT_COMPLETION, {}, key="empty", ticket="a")
    effects = Effects(journal)
    assert effects.recorded("missing") == []
    assert effects.recorded("shared") == ["first", "second"]
    assert effects.recorded("shared", ticket="a") == ["first"]
    assert effects.recorded("shared", ticket="absent") == []
    assert effects.recorded("empty") == [None]

    async def action():
        raise AssertionError("replay ran the action")

    assert await effects.run(action, key="shared", ticket="a") == "first"
