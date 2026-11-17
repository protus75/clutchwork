"""Effect primitive: once-per-key against the surviving journal.

Once is COMPLETION-keyed: a key with a journaled completion replays its recorded
result. An intent with no completion (crash mid-effect) re-executes here on
purpose -- that window belongs to reconcile-on-entry, not this
primitive. A completion may carry a `cost` body field: the ledger folds it.
"""

import json
from collections.abc import Awaitable, Callable
from typing import Any

from clutch.journal import EventType, Journal


class Effects:
    def __init__(self, journal: Journal) -> None:
        self._journal = journal
        # Startup scan; appended to as effects complete: no index builder.
        self._completed = {e.key for e in journal.read() if e.type == EventType.EFFECT_COMPLETION and e.key is not None}

    async def run(
        self,
        action: Callable[[], Awaitable[Any]],
        *,
        key: str,
        ticket: str | None,
        cost: Callable[[Any], dict[str, Any]] | None = None,
    ) -> Any:
        if not isinstance(key, str) or not key:
            raise ValueError(f"effect key must be a non-empty string, got {key!r}; join components with '/'")
        if key in self._completed:
            return self.recorded(key)[0]

        self._journal.append(EventType.EFFECT_INTENT, {}, ticket=ticket, key=key)
        result = await action()
        try:
            encoded = json.dumps(result)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"effect {key!r} returned a non-JSON result ({exc}); return plain dicts/lists/str/numbers") from exc
        # Return the decoded record, not `result`, so executing and replaying yield identical values.
        recorded = json.loads(encoded)
        body = {"result": recorded} if cost is None else {"result": recorded, "cost": cost(recorded)}
        self._journal.append(EventType.EFFECT_COMPLETION, body, ticket=ticket, key=key)
        self._completed.add(key)
        return recorded

    def recorded(self, key: str, ticket: str | None = None) -> list[Any]:
        return [e.body.get("result") for e in self._journal.read() if e.type == EventType.EFFECT_COMPLETION and e.key == key and (ticket is None or e.ticket == ticket)]
