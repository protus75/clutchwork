"""Continuous foreground lifetime."""

import asyncio
import hashlib
import os
import re
import sys
from collections.abc import Awaitable, Callable, Iterable
from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path

from clutch import git, runner, triage
from clutch.config import ConfigError, snapshot_config
from clutch.daemon import DaemonTasks, TicketWriter, WorkerFailureObserver, WorkerStop, _protected_cleanup, _stop_workers, checkpoint_push
from clutch.drain import record_reoffer, reexec_argv
from clutch.effects import Effects
from clutch.enginelog import engine_log
from clutch.git import GitError
from clutch.journal import TERMINAL_STATES, EventType, JournalCorruption, last_transition, run_seq
from clutch.lockfile import CommitLockTimeout, Lockfile
from clutch.merge import AdmissionBoundary
from clutch.mergequeue import regate_receipts
from clutch.providers import ProviderSetupError
from clutch.redact import Redactor
from clutch.retro import Retro
from clutch.seams import ExecutableNotFound, SubprocessExec
from clutch.status import CLOSED, last_states
from clutch.storm import StormLedger
from clutch.supervise_idle import supervise_idle
from clutch.tickets import IntakeRefused, Ticket, TicketInvalid, _pending, _porcelain, intake, parse_ticket, ticket_path

SERVE_POLL_S = 0.1


class Responsiveness:
    """A round trip through an owned consumer, independent of task existence."""

    def __init__(self) -> None:
        self.request = asyncio.Event()
        self.sent = self.answered = 0

    def ask(self) -> None:
        self.sent += 1
        self.request.set()

    def reply(self) -> None:
        self.answered = self.sent
        self.request.clear()

    def responsive(self) -> bool:
        return self.sent > 0 and self.answered == self.sent

    async def wait(self, work: Awaitable):
        """The consumer stays responsive while owning and awaiting its operation."""
        task = asyncio.ensure_future(work)
        ping = None
        try:
            while not task.done():
                ping = asyncio.create_task(self.request.wait())
                await asyncio.wait((task, ping), return_when=asyncio.FIRST_COMPLETED)
                if ping.done():
                    self.reply()
                else:
                    ping.cancel()
                await asyncio.gather(ping, return_exceptions=True)
            return task.result()
        finally:
            if ping is not None:
                ping.cancel()
                await asyncio.gather(ping, return_exceptions=True)
            if not task.done():
                task.cancel()
            await _protected_cleanup(asyncio.gather(task, return_exceptions=True))


class Serve:
    """One idle composition; only run acquires the lock and starts owned work."""

    def __init__(
        self,
        checkout: runner.Checkout,
        *,
        config_path: Path | None = None,
        read: Callable[[str], str | None],
        stems: Callable[[], Iterable[str]],
        prepare=runner.prepare_pipeline,
        signals: Callable | None = None,
        failure: Callable[[BaseException], None] | None = None,
        argv=("engine", "serve"),
        reexec=None,
    ) -> None:
        from clutch.__main__ import build_daemon_core, build_notifications

        self.argv, self.reexec = tuple(argv), reexec or SubprocessExec()
        self.engine = Path(__file__).resolve().parent.parent
        self.trees = self.upgrade = None
        self.read, self.stems, self.signals = read, stems, signals
        self.prepare = prepare
        self.config_path = config_path
        self.writers: dict[str, TicketWriter] = {}
        self.published: dict[str, tuple[Ticket, str]] = {}
        self.queue = None
        self.scan_snapshot = None
        self.scanned = {}
        self.intake_refusal = None
        self.report_arrivals = set()
        self.report_retry = None
        self.stopping = False
        self.served_retro_id = None
        self.retro = None
        self.retro_task = None
        self.wake = asyncio.Event()
        self.ready = asyncio.Event()
        self.workers: tuple[asyncio.Task, ...] = ()
        self.health_tasks: tuple[asyncio.Task, ...] = ()
        self.background: asyncio.Task | None = None
        self.observation: asyncio.Task | None = None
        self.stopper = self.observer = self.checkpoint = None
        self.responses = tuple(Responsiveness() for _ in range(5))
        self.log = engine_log(checkout.config, Redactor.from_config(checkout.config, checkout.env), checkout.clock)
        self.failure = failure or (lambda exc: self.log.event("worker_failure", error=str(exc)))
        self.notifications = build_notifications(checkout, config_path=config_path, log=self.log)

        async def prepared(local):
            callback = await prepare(local)
            if not isinstance(callback, TicketWriter):
                raise TypeError("serve preparation must return the composed TicketWriter")
            callback.ctx.boundary.select = self.select
            if self.queue is None:
                self.queue = callback.queue
            callback.queue = self.queue
            callback.admission = AdmissionBoundary(callback.ctx, mode="daemon", queue=self.queue, waiting=self.core.admission.waiting_for_merge)

            async def dispatch(ticket):
                if not self.select(ticket, "implement"):
                    self.core.scheduler.update(ticket)
                    return "running"
                try:
                    sha = await local.git.rev_parse(local.repo, f"main:{ticket_path(ticket.stem)}")
                    committed = await local.git._run(local.repo, "show", f"main:{ticket_path(ticket.stem)}")
                except GitError:
                    self.core.scheduler.update(ticket)
                    return "running"
                published = self.published.get(ticket.stem)
                if published is not None and published[0] is ticket and published[1] != sha:
                    try:
                        fresh = parse_ticket(ticket.stem, committed, local.repo)
                    except TicketInvalid:
                        return "running"
                    self.publish(fresh, committed)
                    return "running"
                self.writers[ticket.stem] = callback
                events = local.journal.read()
                latest = (last_transition(events, ticket.stem) or {}).get("to")
                if latest in TERMINAL_STATES:
                    record_reoffer(local.journal, events, ticket.stem, sha)
                runner.mark_running(local.journal, ticket.stem, sha)
                try:
                    return await callback(ticket)
                except Exception as exc:
                    if self.stopping:
                        raise
                    runner.dispatch_exception_terminal(local.journal, ticket.stem, exc)
                    self.log.event("dispatch_exception", stem=ticket.stem, error=f"{type(exc).__name__}: {exc}")
                    return "infra_error"
                finally:
                    latest = last_transition(local.journal.read(), ticket.stem) or {}
                    if latest.get("to") in TERMINAL_STATES - CLOSED:
                        self.core.scheduler.update(ticket)
                    if not callback.continuations and not any(context is callback.ctx and stem in callback.queue.pending.keys() for stem, context in callback.queue.contexts.items()):
                        self.writers.pop(ticket.stem, None)

            return dispatch

        self.core = build_daemon_core(
            checkout,
            config_path=config_path,
            read=read,
            debounce=SERVE_POLL_S,
            quarantined=lambda: set(),
            drought_parked=lambda: set(),
            completed_unmerged=lambda: len(self.queue.pending) if self.queue is not None else 0,
            prepare=prepared,
            log=self.log.event,
        )
        publication: dict[str, str] = {}

        def watched_read(stem):
            text = self.read(stem)
            if text is not None:
                publication[stem] = text
            return text

        def watched_publish(ticket):
            self.publish(ticket, publication.pop(ticket.stem))

        self.core.watcher.read = watched_read
        self.core.watcher.publish = watched_publish
        self.checkout = replace(checkout, control=self.core.control)
        self.control = self.core.control
        assert self.control is not None and self.core.restart is not None
        self.core.restart.admissions = self.reconstruct_admissions
        self.box = self.control._recover.__self__
        self.storm = StormLedger(journal=checkout.journal, clock=checkout.clock)
        self.core.scheduler.continuations = lambda: (c.ticket for w in self.writers.values() for c in w.continuations.values())
        self.core.scheduler.next_stage = self.next_stage
        self.core.scheduler.select = self.select
        self.core.admission.resume = self.resume
        self.settling_verdicts = False
        self.core.restart.owned = lambda: self.settling_verdicts or self.core.admission.occupied() or any(w.continuations for w in self.writers.values())
        self.tasks = DaemonTasks(watcher=self.watch, merge_queue=self.merge, box_consumer=self.box_intake, verdict_consumer=self.verdicts)

    def publish(self, ticket: Ticket, text: str) -> None:
        self.published[ticket.stem] = ticket, git.blob_sha(text.encode())
        self.core.scheduler.update(ticket)

    async def reconstruct_admissions(self):
        events = self.checkout.journal.read()
        receipts = regate_receipts(events)
        retained = {(r["stem"], r["attempt"]): r for r in receipts.values() if r["admission"] == "HELD"}
        live = [r for (stem, attempt), r in retained.items() if run_seq(events, stem) == attempt]
        if not live:
            return
        writer = runner.bind(self.checkout, None)
        self.queue = writer.queue
        writer.admission = AdmissionBoundary(writer.ctx, mode="daemon", queue=self.queue)
        for receipt in live:
            stem = receipt["stem"]
            ticket = await self.queue.retained_ticket(stem, receipt)
            self.queue.offer(ticket, attempt=receipt["attempt"])
            self.writers[stem] = writer

    def healthy(self, component: int) -> bool:
        return bool(self.health_tasks) and not self.health_tasks[component].done() and self.responses[component].responsive()

    def stop(self) -> None:
        self.stopping = True
        self.wake.set()

    def select(self, ticket: Ticket, stage: str) -> bool:
        self.control.poll()
        projection = self.control.projection
        if projection.kill_requested:
            self.stop()
        if ticket.stem not in self.writers and not self.stopping and self.control.providers.active:
            from clutch.config import load_config

            snapshot = load_config(self.config_path, cwd=self.checkout.repo)
            tier, _ = runner.capability(ticket, self.checkout.journal.read())
            drought = self.control.providers.drought(snapshot, tier, "implement")
            if drought:
                self.control.providers.park(ticket.stem, drought)
                return False
        return (
            not self.stopping
            and (self.upgrade is None and not projection.stop_requested and not self.retro_pending() or ticket.stem in self.writers)
            and projection.pause_id is None
            and (self.control.admission is None or self.control.admission in projection.released_hold_ids)
            and not any(target["emitting_origin"] == ticket.stem and target["emitting_stage"] == stage for target in self.storm.held_stages().values())
        )

    def next_stage(self, ticket: Ticket) -> str:
        writer = self.writers.get(ticket.stem)
        prior = writer.continuations.get(ticket.stem) if writer is not None else None
        return prior.next_stage if prior is not None else "implement"

    def resume(self, ticket: Ticket):
        writer = self.writers.get(ticket.stem)
        return writer if writer is not None and ticket.stem in writer.continuations else None

    @asynccontextmanager
    async def mutations(self):
        async with self.core.admission.mutations():
            yield

    async def intake_snapshot(self):
        """Only intake inputs, never journal activity from an implementing run."""
        c = self.checkout
        try:
            directory = c.repo / "tickets"
            listing = tuple(c.fs.entries(directory))
            files = tuple((stem, self.read(stem)) for stem in sorted(self.stems()))
            status = await c.git.status_porcelain(c.repo, "--", "tickets/")
            pending = _pending(c.repo, _porcelain(status))
            head = await c.git.rev_parse(c.repo, "main") if pending else None
            states = last_states(c.journal.read()) if pending else {}
            return listing, files, status, head, tuple((stem, states.get(stem)) for stem in sorted(pending))
        except OSError, GitError:
            # Unknown is work; leave intake to report its normal error under the gate.
            return None

    async def scan(self) -> dict[str, str | None]:
        snapshot = await self.intake_snapshot()
        if snapshot is not None and snapshot == self.scan_snapshot:
            return self.scanned
        if self.stopping:
            return {}
        c = self.checkout
        try:
            await intake(c.repo, c.git, c.journal, c.fs, stems=None)
        except IntakeRefused as exc:
            # A stray staged file belongs to a person; refusing intake must not stop serve or its runs.
            if str(exc) != self.intake_refusal:
                self.intake_refusal = str(exc)
                self.log.event("intake_refused", error=str(exc))
            return self.scanned
        self.intake_refusal = None
        async with c.git.main_write():
            self.scanned = {stem: self.read(stem) for stem in self.stems()}
            # Intake's own stamps and commits must not manufacture another work poll.
            self.scan_snapshot = await self.intake_snapshot()
            return self.scanned

    async def watch(self) -> None:
        response = self.responses[3]

        async def changes():
            previous = {}
            while True:
                try:
                    current = await response.wait(self.scan())
                except CommitLockTimeout as exc:
                    self.control.poll()
                    if self.stopping or self.control.projection.stop_requested or self.control.projection.kill_requested:
                        raise
                    self.log.event("commit_lock_timeout", operation="scan", error=str(exc))
                    await response.wait(self.checkout.sleep(SERVE_POLL_S))
                    continue
                if current == previous:
                    await response.wait(self.checkout.sleep(SERVE_POLL_S))
                    continue
                # Hold selection through parsing/publication, including debounce unwind.
                gate = self.core.scheduler._slot
                await response.wait(gate.__aenter__())
                try:
                    for stem in sorted(previous.keys() | current.keys()):
                        if stem not in previous or previous.get(stem) != current.get(stem):
                            yield stem
                    await response.wait(asyncio.gather(*self.core.watcher._waits.values()))
                finally:
                    await gate.__aexit__(None, None, None)
                previous = current
                await response.wait(self.checkout.sleep(SERVE_POLL_S))

        await self.core.watcher.run(changes())

    async def engine_trees(self):
        output = await self.checkout.git._run(self.engine, "rev-parse", "HEAD:clutch")
        trees = output.splitlines()
        if len(trees) != 1 or any(re.fullmatch(r"[0-9a-f]{40,64}", tree) is None for tree in trees):
            raise ValueError("engine tree ids unavailable")
        return tuple(trees)

    async def check_upgrade(self):
        if self.trees is not None and self.upgrade is None:
            try:
                trees = await self.engine_trees()
            except GitError, ValueError, OSError:
                self.trees = None
                self.log.event("self_upgrade_off", reason="engine checkout tree ids unavailable")
                return
            if trees != self.trees:
                self.upgrade = trees
                self.checkout.journal.append(EventType.SIGNAL, {"signal": "serve_upgrade_pending", "clutch": trees[0]})

    def upgrade_idle(self):
        return (
            self.core.admission.idle()
            and not self.core.scheduler.occupied()
            and not any(w.continuations for w in self.writers.values())
            and (self.queue is None or not self.queue.pending and self.queue.active is None)
        )

    def retro_pending(self):
        request_id = self.control.projection.retro_id
        return request_id is not None and request_id != self.served_retro_id

    async def run_retro(self, request_id):
        async with self.mutations():
            self.control.poll()
            if self.stopping or self.control.projection.stop_requested or self.control.projection.kill_requested:
                return
            c = replace(self.checkout, config=snapshot_config(self.control.load_config()))
            pipeline = await self.prepare(c)
            self.retro = Retro(c, pipeline)
            try:
                await self.retro(forced=request_id is not None)
                self.served_retro_id = request_id if request_id is not None else self.served_retro_id
            finally:
                self.retro = None

    async def dispatch(self) -> None:
        response = self.responses[0]
        while True:
            self.core.scheduler.raise_failure()
            busy = self.core.admission.busy()
            exclusive_pending = self.core.admission.exclusive_pending()
            self.control.poll()
            if self.control.projection.kill_requested:
                self.stop()
            if not self.stopping and self.control.projection.pause_id is None:
                if not busy:
                    await response.wait(self.check_upgrade())
                    if self.upgrade_idle() and not self.control.projection.stop_requested:

                        async def supervise():
                            async with self.mutations():
                                self.control.poll()
                                if self.stopping or self.control.projection.stop_requested or self.control.projection.kill_requested or self.control.projection.pause_id is not None:
                                    return

                                async def make_ctx():
                                    return (await self.prepare(replace(self.checkout, config=snapshot_config(self.control.load_config())))).ctx

                                async def run_triage(ids):
                                    from clutch.__main__ import _preflighted_llm
                                    from clutch.box import UnknownBoxId

                                    try:
                                        llm = await _preflighted_llm(self.checkout, self.control.providers)
                                        await triage.triage_pass(self.checkout, llm, frozenset(ids))
                                    except UnknownBoxId as exc:
                                        self.log.event("triage_refused", reason=str(exc))
                                        raise

                                await self.control.inbox.settle_triage(run_triage)
                                await supervise_idle(self.checkout, make_ctx)

                        await response.wait(supervise())
                if not busy or not exclusive_pending:
                    await response.wait(self.core.scheduler.dispatch_next())
            await response.wait(self.checkout.sleep(SERVE_POLL_S))

    async def apply_verdict(self, stem, verb, key, actor, reason=None):
        result = await runner.apply_admission(stem, verb, key, actor, self.checkout, **({"reason": reason} if reason is not None else {}))
        if result["refusal"] is not None:
            self.log.event("verdict_refused", stem=stem, verb=verb, reason=result["refusal"])
        elif verb == "confirm" and stem in self.published:
            self.core.scheduler.update(self.published[stem][0])
        return result

    def merge_work(self) -> bool:
        projection = self.control.projection
        if projection.stop_requested or projection.kill_requested:
            return True
        queue = self.queue
        if queue is None:
            return False
        released = queue.paused and queue.hold_id in projection.released_hold_ids
        return bool(
            queue.active is not None
            or released
            or (queue.pending and not queue.paused)
            or any(stem not in self.core.admission.runs and not w.continuations and stem not in queue.pending for stem, w in self.writers.items())
        )

    async def merge(self) -> None:
        response = self.responses[1]

        async def poll():
            if self.queue is not None:
                await self.check_upgrade()
            if not self.merge_work():
                return
            async with self.core.admission.merging():
                self.control.poll()
                if self.stopping or self.control.projection.kill_requested:
                    return
                if self.queue is None:
                    return
                self.queue.deliveries = []
                await self.queue.process()
                for ticket, attempt, result in self.queue.deliveries:
                    owner = self.writers.get(ticket.stem) or next(w for w in self.writers.values() if w.ctx is self.queue.contexts.get(ticket.stem))
                    self.writers[ticket.stem] = owner
                    await owner.consume_result(ticket, result, attempt=attempt)
                    latest = (last_transition(self.checkout.journal.read(), ticket.stem) or {}).get("to")
                    if latest in TERMINAL_STATES - CLOSED:
                        self.core.scheduler.update(ticket)
                    if ticket.stem not in self.queue.pending:
                        self.queue.contexts.pop(ticket.stem, None)
                for stem, writer in tuple(self.writers.items()):
                    if stem not in self.core.admission.runs and not writer.continuations and stem not in self.queue.pending:
                        del self.writers[stem]

        while True:
            await response.wait(poll())
            await response.wait(self.checkout.sleep(SERVE_POLL_S))

    async def verdicts(self) -> None:
        response = self.responses[4]
        while True:
            self.control.poll()
            if not self.stopping and not self.control.projection.kill_requested:
                self.settling_verdicts = True
                try:
                    await response.wait(self.control.inbox.settle_admissions(self.apply_verdict))
                finally:
                    self.settling_verdicts = False
            await response.wait(self.checkout.sleep(SERVE_POLL_S))

    def box_work(self) -> bool:
        """New reports are immediate; failed arrivals retry on the injected clock."""
        config = self.control.load_config()
        if config.report_inbox is None:
            return False
        try:
            expected, recorded, _ = self.storm._evidence()
            origins = {m.origin for m in self.box.messages()} if expected else set()
            if any(identity not in recorded or "storm-breaker/" + identity not in origins for identity in expected):
                return True
            pending = set()
            for path in config.report_inbox.glob("*.json"):
                arrival = hashlib.sha256(str(path.resolve()).encode()).hexdigest()
                if "consumed" not in self.checkout.fs.entries(self.box.root / "custody" / arrival):
                    pending.add(arrival)
            now = self.checkout.clock()
            return bool(pending - self.report_arrivals or pending and (self.report_retry is None or (now - self.report_retry).total_seconds() >= 30))
        except OSError:
            return True

    async def box_intake(self) -> None:
        response = self.responses[2]

        async def poll():
            if not self.box_work():
                return
            async with self.mutations():
                if self.stopping:
                    return
                c = replace(self.checkout, config=snapshot_config(self.control.load_config()))
                self.report_retry = c.clock()
                if c.config.report_inbox is not None:
                    self.report_arrivals.update(hashlib.sha256(str(path.resolve()).encode()).hexdigest() for path in c.config.report_inbox.glob("*.json"))
                triage.report_intake(c)

        while True:
            await response.wait(poll())
            await response.wait(self.checkout.sleep(SERVE_POLL_S))

    async def abort(self) -> None:
        operations = set(self.core.admission.runs.values()) | {task for task in (self.core.admission.mutating,) if task is not None}
        aborts = [writer.abort_current for writer in tuple(self.writers.values())]
        if self.retro is not None:
            aborts.append(self.retro.abort_current)
        errors = []
        for abort in aborts:
            try:
                await abort()
            except BaseException as exc:
                errors.append(exc)
        # Observe preparation and non-model process operations before WorkerStop touches workers.
        for task in operations:
            if not task.done() and not task.cancelling():
                task.cancel()
        for task in operations:
            cleanup = asyncio.gather(task, return_exceptions=True)
            await _protected_cleanup(cleanup)
            errors.extend(result for result in cleanup.result() if isinstance(result, BaseException) and not isinstance(result, asyncio.CancelledError))
        if errors:
            raise errors[0]

    async def cleanup(self) -> None:
        await self.ready.wait()
        abort_error = None
        errors = []
        try:
            await self.stopper.stop(replace(self.control.projection, kill_requested=True))
        except BaseException as exc:
            abort_error = exc
        finally:
            # Even a failed abort has unwound before worker cleanup. It cannot earn kill_applied.
            await _protected_cleanup(_stop_workers(self.workers))
            try:
                await self.core.scheduler.close()
            except Exception as exc:
                errors.append(exc)
            await _protected_cleanup(asyncio.create_task(self.notifications.close()))
        results = await asyncio.gather(self.background, self.observation, return_exceptions=True)
        errors += [task.exception() for task in self.workers if not task.cancelled()]
        errors += [r for r in results if isinstance(r, BaseException)]
        for writer in self.writers.values():
            writer.continuations.clear()
        if abort_error is not None:
            raise abort_error
        for error in errors:
            if isinstance(error, BaseException) and not isinstance(error, asyncio.CancelledError):
                raise error

    async def maintenance(self) -> None:
        self.control.poll()
        if self.control.projection.kill_requested:
            self.stop()
        if self.stopping:
            return
        self.core.restart.timers.fire_due()
        if not self.core.admission.busy() and not self.core.scheduler.occupied():
            await self.core.sweep_orphans()
            async with self.core.admission.exclusive():
                self.box.recover()
                await self.checkpoint.poll()
        self.notifications.poll()

    async def run(self) -> int:
        c = self.checkout
        lock = Lockfile(c.config.state_dir, verb="serve", instance_id=await c.git.describe(c.repo), clock=c.clock)
        pid = os.getpid()
        lock.acquire()

        def restore():
            return None

        code = 0
        upgrade_stop = False
        failure_type = None
        handoff = False
        try:
            self.log.event("engine_start", verb="serve", pid=pid)
            try:
                try:
                    self.trees = await self.engine_trees()
                except Exception:
                    self.log.event("self_upgrade_off", reason="engine checkout tree ids unavailable")
                await self.core.startup()
                self.notifications.poll(startup=True)
            except Exception as exc:
                raise runner.Refusal(f"serve startup recovery refused: {exc}", "repair the recovery evidence and start serve again") from exc
            self.control.publish()
            if self.signals is not None:
                restore = self.signals(self.stop)
            self.checkpoint = checkpoint_push(c.repo, journal=c.journal, effects=Effects(c.journal), git=c.git, box=self.box, log=self.log)
            # Guard only this lifetime: the component's ordinary run semantics stay intact.
            pending_failure = None

            async def guarded(callback):
                nonlocal pending_failure, code, failure_type
                try:
                    await callback()
                    raise RuntimeError("owned serve consumer returned unexpectedly")
                except BaseException as exc:
                    # Latch before DaemonTasks cancels siblings; those cancellations
                    # belong to this lifetime's cleanup, not another worker failure.
                    if not self.stopping and not self.control.projection.kill_requested:
                        pending_failure = exc
                        failure_type = type(exc).__name__
                        code = 2 if isinstance(exc, (ConfigError, runner.Refusal, ProviderSetupError, JournalCorruption, ExecutableNotFound)) else 1
                    self.stop()
                    raise

            def observed_failure(_exc):
                nonlocal pending_failure
                if pending_failure is not None:
                    exc, pending_failure = pending_failure, None
                    self.failure(exc)

            self.tasks._consumers = tuple((lambda callback=callback: guarded(callback)) for callback in self.tasks._consumers)

            def bind(tasks):
                self.workers = (worker, *tasks)
                self.health_tasks = (worker, tasks[1], tasks[2], tasks[0], tasks[3])
                self.stopper = WorkerStop(lifecycle_id=self.control.projection.lifecycle_id, abort=self.abort, workers=self.workers)
                self.observer = WorkerFailureObserver(lifecycle_id=self.control.projection.lifecycle_id, workers=self.workers, projection=lambda: self.control.projection, failure=observed_failure)
                self.observation = asyncio.create_task(self.observer.observe())
                self.ready.set()

            self.tasks.started = bind
            self.background = asyncio.create_task(self.tasks.run())
            worker = asyncio.create_task(guarded(self.dispatch))
            try:
                await self.ready.wait()
                while not self.stopping:
                    await self.maintenance()
                    if (self.upgrade is not None or self.control.projection.stop_requested) and self.upgrade_idle() and not self.stopping:
                        self.control.poll()
                        if self.control.projection.kill_requested:
                            self.stop()
                        else:
                            upgrade_stop = not self.control.projection.stop_requested
                            self.stop()
                            break
                    if self.retro_task is not None and self.retro_task.done():
                        self.retro_task.result()
                        self.retro_task = None
                    if self.retro_task is None and self.retro_pending() and self.upgrade is None and not self.control.projection.stop_requested and self.upgrade_idle():
                        request_id = self.control.projection.retro_id
                        if request_id == self.served_retro_id:
                            request_id = None
                        self.retro_task = asyncio.create_task(self.run_retro(request_id))
                    for response in self.responses:
                        response.ask()
                    done = [task for task in self.workers if task.done()]
                    if done:
                        for task in done:
                            if task.cancelled():
                                raise RuntimeError("owned serve consumer cancelled unexpectedly")
                            task.result()
                        raise RuntimeError("owned serve consumer stopped unexpectedly")
                    sleeping = asyncio.create_task(c.sleep(SERVE_POLL_S))
                    stopping = asyncio.create_task(self.wake.wait())
                    try:
                        await asyncio.wait((sleeping, stopping), return_when=asyncio.FIRST_COMPLETED)
                    finally:
                        sleeping.cancel()
                        stopping.cancel()
                        await _protected_cleanup(asyncio.gather(sleeping, stopping, return_exceptions=True))
            except asyncio.CancelledError:
                self.stop()
            except Exception as exc:
                failure_type = type(exc).__name__
                self.log.event("serve_failed", error=str(exc))
                code = 2 if isinstance(exc, (ConfigError, runner.Refusal, ProviderSetupError, JournalCorruption, ExecutableNotFound)) else 1
                self.stop()
            self.control.poll()
            handoff = upgrade_stop and self.upgrade is not None and self.upgrade_idle() and not self.control.projection.kill_requested and code == 0
            if handoff:
                c.journal.append(EventType.SIGNAL, {"signal": "serve_handoff", "clutch": self.upgrade[0]})
            cleanup = asyncio.create_task(self.control.apply_kill(self.cleanup) if self.control.projection.kill_requested else self.cleanup())
            try:
                await _protected_cleanup(cleanup)
            except asyncio.CancelledError:
                if cleanup.cancelled():
                    failure_type = "CancelledError"
                    code = 1
            except Exception as exc:
                failure_type = type(exc).__name__
                self.log.event("serve_cleanup_failed", error=str(exc))
                if code != 2:
                    code = 1
            self.control.poll()
            handoff = handoff and not self.control.projection.kill_requested and not self.control.projection.stop_requested and code == 0
            if handoff:
                c.journal.close()
        finally:
            try:
                await _protected_cleanup(asyncio.create_task(self.notifications.close()))
                await _protected_cleanup(asyncio.create_task(self.control.providers.close()))
            finally:
                try:
                    self.control.retire()
                finally:
                    try:
                        restore()
                    finally:
                        try:
                            exc = sys.exception()
                            outcome = (
                                f"error: {type(exc).__name__}"
                                if exc
                                else f"error: {failure_type}"
                                if failure_type
                                else "killed"
                                if self.control.projection.kill_requested
                                else "handoff"
                                if handoff
                                else "stopped"
                            )
                            self.log.event("engine_stop", verb="serve", pid=pid, outcome=outcome)
                        finally:
                            lock.release()
        if handoff:
            code = await self.reexec.replace(reexec_argv(self.argv, engine=self.engine), cwd=c.repo, env=c.env)
        return code


async def serve(
    checkout: runner.Checkout,
    *,
    config_path: Path | None = None,
    read: Callable[[str], str | None] | None = None,
    stems: Callable[[], Iterable[str]] | None = None,
    prepare=runner.prepare_pipeline,
    signals: Callable | None = None,
    failure: Callable[[BaseException], None] | None = None,
    argv=("engine", "serve"),
    reexec=None,
) -> int:
    from clutch.__main__ import build_serve

    owner = build_serve(checkout, config_path=config_path, read=read, stems=stems, prepare=prepare, signals=signals, failure=failure, argv=argv, reexec=reexec)
    return await owner.run()
