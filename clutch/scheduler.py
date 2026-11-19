"""Single-flight dispatch projection."""

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Set
from pathlib import Path

from clutch.config import Caps
from clutch.drain import authored_at, order_tickets, parked_blob, reofferable, write_queue
from clutch.journal import TERMINAL_STATES, Journal
from clutch.seams import Clock, FileSystem
from clutch.status import CLOSED, last_states
from clutch.tickets import Ticket


class Scheduler:
    def __init__(
        self,
        journal: Journal,
        dispatch: Callable[[Ticket], Awaitable[object]],
        *,
        state_dir: Path,
        fs: FileSystem,
        clock: Clock,
        caps: Callable[[], Caps],
        ticket_sha: Callable[[str], Awaitable[str]],
        quarantined: Callable[[], Set[str]],
        drought_parked: Callable[[], Set[str]],
        completed_unmerged: Callable[[], int],
        max_unmerged: int,
    ) -> None:
        self.state_dir, self.fs, self.clock = state_dir, fs, clock
        self.journal = journal
        self.dispatch = dispatch
        self.caps = caps
        self.ticket_sha = ticket_sha
        self.quarantined = quarantined
        self.drought_parked = drought_parked
        self.completed_unmerged = completed_unmerged
        self.max_unmerged = max_unmerged
        self.pending: dict[str, Ticket] = {}
        self._slot = asyncio.Lock()
        self.continuations: Callable[[], Iterable[Ticket]] = lambda: ()
        self.next_stage: Callable[[Ticket], str] = lambda _: "implement"
        self.select: Callable[[Ticket, str], bool] = lambda _ticket, _stage: True

    def occupied(self) -> bool:
        return self._slot.locked()

    def update(self, ticket: Ticket) -> None:
        self.pending[ticket.stem] = ticket

    def remove(self, stem: str) -> None:
        self.pending.pop(stem, None)

    async def dispatch_next(self) -> Ticket | None:
        """Concurrent requests wait for completion, then select from current projections."""
        async with self._slot:
            events = self.journal.read()
            last = last_states(events)
            held = self.quarantined() | self.drought_parked()
            if self.completed_unmerged() >= self.max_unmerged:
                return None
            from clutch.rework import settled_dependencies, supersedes_maps

            settled = settled_dependencies(events)
            maps = supersedes_maps(events)
            authored = authored_at(events)
            retained = {t.stem: t for t in self.continuations()}
            candidates = {**self.pending, **retained}
            for stem in candidates:
                if (blob := parked_blob(events, stem)) is not None and blob == await self.ticket_sha(stem):
                    held.add(stem)
            ready = [
                t
                for t in candidates.values()
                if t.frontmatter.state == "confirmed"
                and last.get(t.stem) not in CLOSED
                and (last.get(t.stem) != "running" or t.stem in retained)
                and (last.get(t.stem) not in TERMINAL_STATES or reofferable(events, t.stem, self.caps()))
                and t.stem not in held
                and t.stem not in maps
                and set(t.depends) <= settled
                and self.select(t, self.next_stage(t))
            ]
            if not ready:
                return None
            ordered = order_tickets(ready, authored)
            write_queue(self.state_dir, self.fs, self.clock, ordered)
            ticket = ordered[0]
            self.remove(ticket.stem)
            await self.dispatch(ticket)
            return ticket
