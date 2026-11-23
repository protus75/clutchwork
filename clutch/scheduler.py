"""Slot-limited dispatch projection and run task ownership."""

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Set
from pathlib import Path

from clutch.caps import conflict_reruns
from clutch.config import Caps, Parallel
from clutch.drain import SKIP_LIMIT, authored_at, eligible, fill_slots, order_tickets, parallel_order, parked_blob, reofferable, write_queue
from clutch.journal import TERMINAL_STATES, Journal
from clutch.seams import Clock, FileSystem
from clutch.status import last_states
from clutch.tickets import Ticket, fences_overlap


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
        self.flying: dict[str, Ticket] = {}
        self.skips: dict[str, int] = {}
        self.last_queue_reason = None
        self.tasks: set[asyncio.Task] = set()
        self.failures: list[BaseException] = []
        self.parallel: Callable[[], Parallel] = Parallel
        self.log: Callable[..., None] = lambda *args, **kwargs: None
        self._slot = asyncio.Lock()
        self.flake_fixes: Callable[[], Set[str]] = lambda: set()
        self.continuations: Callable[[], Iterable[tuple[Ticket, str | None]]] = lambda: ()
        self.next_stage: Callable[[Ticket], str] = lambda _: "implement"
        self.select: Callable[[Ticket, str], bool] = lambda _ticket, _stage: True

    def occupied(self) -> bool:
        return self._slot.locked() or bool(self.flying) or bool(self.failures)

    def raise_failure(self) -> None:
        if self.failures:
            raise self.failures.pop(0)

    async def close(self) -> None:
        tasks = tuple(self.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.flying.clear()
        self.raise_failure()

    def update(self, ticket: Ticket) -> None:
        self.pending[ticket.stem] = ticket

    def remove(self, stem: str) -> None:
        self.pending.pop(stem, None)

    async def dispatch_next(self) -> Ticket | None:
        """Select from current projections and return once a run occupies a slot."""
        self.raise_failure()
        async with self._slot:
            events = self.journal.read()
            last = last_states(events)
            held = self.quarantined() | self.drought_parked()
            parallel = self.parallel()
            if (not parallel.enabled and self.flying) or (parallel.enabled and len(self.flying) >= parallel.max_runs):
                return None
            from clutch.rework import settled_dependencies, supersedes_maps

            settled = settled_dependencies(events)
            maps = supersedes_maps(events)
            authored = authored_at(events)
            retained = {}
            for ticket, sha in self.continuations():
                if last.get(ticket.stem) == "running" or sha is not None and sha == await self.ticket_sha(ticket.stem):
                    retained[ticket.stem] = ticket
            candidates = {**self.pending, **retained}
            for stem in candidates:
                if (blob := parked_blob(events, stem)) is not None and blob == await self.ticket_sha(stem):
                    held.add(stem)
            ready = [
                t
                for t in eligible(candidates.values(), last, settled, maps)
                if (last.get(t.stem) != "running" or t.stem in retained)
                and (last.get(t.stem) not in TERMINAL_STATES or reofferable(events, t.stem, self.caps()))
                and t.stem not in held
                and self.select(t, self.next_stage(t))
            ]
            if not ready:
                return None
            hold = "max_unmerged" if self.completed_unmerged() >= self.max_unmerged else None
            waiting = {}
            if parallel.enabled:
                unsettled = {stem: t for stem, t in candidates.items() if stem not in settled} | self.flying
                ordered = parallel_order(ready, authored, unsettled, fixes=self.flake_fixes())
                rerun = {stem for stem in candidates.keys() | self.flying.keys() if conflict_reruns(events, stem) > 0}
                selected, counts = fill_slots(ordered, self.flying.values(), 1, parallel.shared_paths, self.skips, rerun) if not hold else ([], self.skips)
                occupied = list(self.flying.values())
                for candidate in ordered:
                    if candidate in selected or hold:
                        break
                    overlaps = sorted(other.stem for other in occupied if fences_overlap(candidate, other, parallel.shared_paths, rerun))
                    if overlaps:
                        waiting[candidate.stem] = overlaps
                        if self.skips.get(candidate.stem, 0) >= SKIP_LIMIT:
                            occupied.append(candidate)
                for stem, count in counts.items():
                    if count > self.skips.get(stem, 0):
                        self.log("dispatch_skip", stem=stem, count=count)
                self.skips = counts
                if selected:
                    ticket = selected[0]
                    ordered = [ticket, *(t for t in ordered if t.stem != ticket.stem)]
            else:
                ordered = order_tickets(ready, authored, fixes=self.flake_fixes())
                ticket = ordered[0] if not hold else None
            if hold or (parallel.enabled and not selected):
                reason = (waiting, hold)
                if reason != self.last_queue_reason:
                    write_queue(self.state_dir, self.fs, self.clock, ordered, waiting, hold)
                    self.last_queue_reason = reason
                return None
            write_queue(self.state_dir, self.fs, self.clock, ordered, waiting, hold)
            self.last_queue_reason = (waiting, hold)
            self.remove(ticket.stem)
            self.flying[ticket.stem] = ticket
            task = asyncio.create_task(self.dispatch(ticket))
            self.tasks.add(task)

            def done(task: asyncio.Task) -> None:
                self.tasks.remove(task)
                del self.flying[ticket.stem]
                if not task.cancelled() and (error := task.exception()) is not None:
                    self.failures.append(error)

            task.add_done_callback(done)
            return ticket
