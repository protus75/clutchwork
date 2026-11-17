"""The CLI module entry: `uv run python -m clutch <verb>`.

The composition root: the only place real seams are constructed. Exit 2 is an engine-plane refusal.
"""

import argparse
import asyncio
import json
import os
import re
import signal
import subprocess
import sys
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence, Set
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import yaml

import clutch
from clutch import ask, control, drain, hostfiles, issue, observe, reconcile, requisition, runner, seams, serve, triage
from clutch.box import UnknownBoxId
from clutch.config import ConfigError, ConfigSnapshot, load_config, load_config_text, migrate_config
from clutch.daemon import DaemonCore, PauseConsumer, StartupBoundary, daemon_core
from clutch.git import Git, GitError
from clutch.journal import EventType, Journal, JournalCorruption, last_transition
from clutch.llm import TIERS, LLMRequest
from clutch.lockfile import ENGINE_VERBS, CommitLock, CommitLockTimeout, Lockfile, LockHeld
from clutch.notify import NOTIFY_TIMEOUT_S, NotificationReconciler
from clutch.providers import (
    ADAPTERS,
    INSTALL_TIMEOUT_S,
    PLACEHOLDER,
    PREFLIGHT_TIMEOUT_S,
    PROBE_PROMPT,
    ProviderLLM,
    ProviderSession,
    ProviderSetupError,
    child_env,
    cli_status,
    routed_conduct_paths,
    suggest_config,
    tool_env,
)
from clutch.redact import Redactor
from clutch.restart import Restart
from clutch.seams import Clock, CommandNotifications, ExecutableNotFound, LocalFileSystem, ProcessExec, SubprocessExec
from clutch.status import last_states, lint_admission, order_admission, project, reject_queue, render, review_admission
from clutch.storm import StormLedger
from clutch.tickets import (
    KINDS,
    PRIORITIES,
    IntakeRefused,
    Ticket,
    TicketInvalid,
    _intake_claims,
    _load_frontmatter,
    _pending,
    _porcelain,
    evidence_findings,
    lint_findings,
    missing_evidence_findings,
    order,
    split_frontmatter,
    stem_findings,
    template,
    ticket_path,
    validate_ticket,
)
from clutch.timers import Timers

GIT_TIMEOUT_S = 30.0


def _config_reloader(path, repo):
    return lambda: load_config(path, cwd=repo)


def _observe_context(repo, config, config_path, exec_, git, env):
    return observe.Context(repo.resolve(), config.state_dir.resolve(), (config_path or repo / "config.yaml").resolve(), exec_, git, child_env(env, config))


def _fail(verb, message):
    print(f"clutch {verb}: {message}", file=sys.stderr)
    return runner.EXIT_REFUSED


@asynccontextmanager
async def _locked(state_dir, verb, *, instance_id, clock):
    lock = Lockfile(state_dir, verb=verb, instance_id=instance_id, clock=clock)
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def _clock() -> datetime:
    return datetime.now(UTC)


async def _preflighted_llm(checkout: runner.Checkout, session: ProviderSession) -> ProviderLLM:
    llm = ProviderLLM(checkout.config, exec_=checkout.exec_, fs=checkout.fs, env=checkout.env, cwd=checkout.repo, timeout=runner.call_timeout(checkout.config), session=session)
    session.timers.reconstruct()
    session.timers.fire_due()
    problems = await llm.preflight() if session.active else []
    if problems:
        raise ProviderSetupError("; ".join(problems))
    return llm


def build_control(checkout: runner.Checkout) -> PauseConsumer:
    """Compose without reading requests, publishing discovery, or starting tasks."""
    from clutch.daemon import storm_producer

    box = storm_producer(root=checkout.config.state_dir / "box", fs=checkout.fs, journal=checkout.journal, clock=checkout.clock)
    consumer = PauseConsumer(
        journal=checkout.journal,
        lifecycle_id=uuid4().hex,
        state_dir=checkout.config.state_dir,
        fs=checkout.fs,
        sleep=checkout.sleep,
        files=lambda: (checkout.config.state_dir / "control/inbox").glob("*"),
        read=Path.read_bytes,
        known=lambda stem: (checkout.repo / ticket_path(stem)).is_file() or any(e.ticket == stem for e in checkout.journal.read()),
        recover=box.recover,
        storm_holds=StormLedger(journal=checkout.journal, clock=checkout.clock).holds,
    )
    timers = Timers(journal=checkout.journal, clock=checkout.clock, sleep=checkout.sleep)
    consumer.providers = ProviderSession(checkout.config, journal=checkout.journal, clock=checkout.clock, sleep=checkout.sleep, timers=timers)
    consumer.load_config = _config_reloader(None, checkout.repo)
    return consumer


def build_daemon_core(
    checkout: runner.Checkout,
    *,
    config_path: Path | None = None,
    read: Callable[[str], str | None],
    debounce: float,
    quarantined: Callable[[], Set[str]],
    drought_parked: Callable[[], Set[str]],
    completed_unmerged: Callable[[], int],
    prepare: Callable[[runner.Checkout], Awaitable[runner.Dispatch]] = runner.prepare_pipeline,
) -> DaemonCore:
    """Compose the production core without starting consumers or preparing a dispatch."""
    consumer = checkout.control or build_control(checkout)
    consumer.load_config = _config_reloader(config_path, checkout.repo)
    checkout = replace(checkout, control=consumer)

    def bind(snapshot: ConfigSnapshot) -> runner.Dispatch:
        local = replace(checkout, config=snapshot)

        async def dispatch(ticket: Ticket) -> str:
            callback = await prepare(local)
            tier, _ = runner.capability(ticket, checkout.journal.read())
            drought = consumer.providers.drought(snapshot, tier, "implement") if consumer.providers.active else None
            if drought:
                consumer.providers.park(ticket.stem, drought)
                core.scheduler.update(ticket)
                return "infra_error"
            result = await callback(ticket)
            history = checkout.journal.read()
            body = last_transition(history, ticket.stem) or {}
            if "provider_drought" in body:
                core.scheduler.update(ticket)
            return result

        return dispatch

    core = daemon_core(
        checkout.repo,
        journal=checkout.journal,
        state_dir=checkout.config.state_dir,
        fs=checkout.fs,
        load=_config_reloader(config_path, checkout.repo),
        bind=bind,
        read=read,
        ticket_sha=lambda stem: checkout.git.rev_parse(checkout.repo, f"HEAD:tickets/{stem}/ticket.md"),
        clock=checkout.clock,
        sleep=checkout.sleep,
        debounce=debounce,
        quarantined=quarantined,
        drought_parked=drought_parked,
        completed_unmerged=completed_unmerged,
        max_unmerged=checkout.config.scheduler.max_unmerged,
        before_dispatch=consumer.checkpoint,
        control=consumer,
    )
    timers = consumer.providers.timers
    restart = Restart(checkout, timers=timers, owned=lambda: core.admission.active is not None or core.admission.task is not None)
    core.admission.restart = restart
    core.admission._before_dispatch = StartupBoundary(restart, consumer).checkpoint

    def provider_holds():
        held = set(drought_parked())
        latest = {}
        for event in checkout.journal.read():
            if event.type == "state_transition" and event.ticket is not None:
                latest[event.ticket] = event.body
        for stem, body in latest.items():
            if route := body.get("provider_drought"):
                snapshot = load_config(config_path, cwd=checkout.repo)
                if consumer.providers.drought(snapshot, route["tier"], route["surface"]):
                    held.add(stem)
        return held

    core.scheduler.drought_parked = provider_holds
    return core


def build_serve(checkout: runner.Checkout, *, config_path=None, read=None, stems=None, prepare=runner.prepare_pipeline, signals=None, failure=None, argv=("serve",), reexec=None) -> serve.Serve:
    """Compose filesystem delivery at the same root as every other real seam."""

    def read_ticket(stem):
        path = checkout.repo / ticket_path(stem)
        return path.read_text() if path.is_file() else None

    return serve.Serve(
        checkout,
        config_path=config_path,
        read=read or read_ticket,
        stems=stems or (lambda: (p.parent.name for p in (checkout.repo / "tickets").glob("*/ticket.md"))),
        prepare=prepare,
        signals=signals,
        failure=failure,
        argv=argv,
        reexec=reexec,
    )


def build_notifications(checkout: runner.Checkout, *, config_path: Path | None, log) -> NotificationReconciler:
    executor = SubprocessExec()  # Never alias active work or the self-upgrade handoff.

    def compose(config):
        return CommandNotifications(executor, cwd=checkout.repo, env=child_env(checkout.env, config, serving=None), timeout=NOTIFY_TIMEOUT_S, scrub=Redactor.from_config(config, checkout.env).scrub)

    return NotificationReconciler(
        journal=checkout.journal, clock=checkout.clock, config_path=config_path or checkout.repo / "config.yaml", load=_config_reloader(config_path, checkout.repo), compose=compose, log=log
    )


def build_driver():
    async def step(checkout, log):
        from clutch import roadmap

        async def author_messages(ids):
            llm = await _preflighted_llm(checkout, checkout.control.providers)
            await triage.triage_pass(checkout, llm, frozenset(ids))

        notifications = CommandNotifications(
            SubprocessExec(), cwd=checkout.repo, env=child_env(checkout.env, checkout.config, serving=None), timeout=NOTIFY_TIMEOUT_S, scrub=Redactor.from_config(checkout.config, checkout.env).scrub
        )
        return await roadmap.drive(checkout, author_messages=author_messages, notifications=notifications, log=log)

    return step


def watchdog_observation(workspace: Path, fence):
    from clutch.watchdog import ScopeObservation

    def snapshot():
        files = {}
        for prefix in fence:
            path = workspace / prefix
            paths = path.rglob("*") if path.is_dir() else (path,)
            for candidate in paths:
                if candidate.is_file():
                    files[candidate.relative_to(workspace).as_posix()] = candidate.read_bytes()
        return files

    return ScopeObservation(fence, snapshot)


def watchdog_notifications(config, env, effects, log, *, redactor, cwd, **context):
    from clutch.notify import WatchdogNotifications

    return WatchdogNotifications(
        effects=effects,
        notifications=CommandNotifications(SubprocessExec(), cwd=cwd, env=child_env(env, config, serving=None), timeout=NOTIFY_TIMEOUT_S, scrub=redactor.scrub),
        argv=config.notify,
        log=log,
        **context,
    )


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m clutch", description="Host guides: clutch docs")
    ap.add_argument("--config", type=Path, help="config path (default: config.yaml at the checkout root)")
    sub = ap.add_subparsers(dest="verb", required=True)
    sub.add_parser("watch", help="read-only live engine view").add_argument("--once", action="store_true")
    sub.add_parser("snapshot", help="read-only JSON snapshot")
    sub.add_parser("status", help="project current state from the journal (read-only)")
    stats = sub.add_parser("stats", help="project journal health over a window (read-only)")
    stats.add_argument("--window", default="7d")
    stats.add_argument("--json", action="store_true")
    stats.add_argument("--tree", action="store_true")
    sub.add_parser("lint", help="validate tickets without running or writing anything").add_argument("stems", nargs="*")
    sub.add_parser("retro", help="run a retro now, or queue one on the running engine")
    sub.add_parser("doctor", help="inspect setup without changing state")
    sub.add_parser("core", help="refresh managed conduct in every routed agent's root file")
    prompt = sub.add_parser("prompt", help="render an operator prompt")
    prompt.add_argument("kind", choices=ask.KINDS)
    prompt.add_argument("stems", nargs="*")
    sub.add_parser("docs", help="print installed host guide paths")
    sub.add_parser("init-config", help="print a suggested config.yaml from the provider CLIs found").add_argument("--write", action="store_true")
    sub.add_parser("install", help="install provider CLIs into the host project as pnpm dev dependencies").add_argument("providers", nargs="*")
    sub.add_parser("update-config", help="list the model names each declared provider serves and compare them with config.yaml")
    sub.add_parser("probe", help="probe declared providers").add_argument("providers", nargs="*")
    sub.add_parser("migrate-config", help="validate and migrate schema_version: 0 to the current config schema")
    for verb in ("pause", "resume"):
        sub.add_parser(verb, help=f"submit {verb} to the running engine, or do nothing under the idle lock")
    sub.add_parser("kill", help="submit kill to the running engine; refuse when nothing is running")
    sub.add_parser("stop", help="finish the running ticket, admit nothing new, then exit")
    sub.add_parser("review", help="review a committed ticket against merged code and journal its verdict").add_argument("stems", nargs="+")
    sub.add_parser("suggest", help="queue an idea for triage").add_argument("summary")
    issue_parser = sub.add_parser("issue", help="print a prefilled GitHub new-issue link for a critical clutch bug")
    issue_parser.add_argument("--class", dest="issue_class", default=None, help=", ".join(issue.CLASSES))
    issue_parser.add_argument("title")
    issue_parser.add_argument("--body", type=Path, required=True)
    sub.add_parser("triage", help="make one sequential pass over pending suggestions under the lock").add_argument("ids", nargs="*")
    roadmap = sub.add_parser("roadmap", help="maintain roadmap tickets")
    roadmap_sub = roadmap.add_subparsers(dest="roadmap_verb", required=True)
    from clutch.roadmap import AHEAD

    roadmap_sub.add_parser("author", help="author ready roadmap rows").add_argument("--ahead", type=int, default=AHEAD)
    roadmap_sub.add_parser("status", help="show read-only roadmap progress")
    roadmap_sub.add_parser("accept", help="review a release against its promises").add_argument("release")
    roadmap_sub.add_parser("gate", help="run a release's ship gate").add_argument("release")
    merged = roadmap_sub.add_parser("merged", help="check merged roadmap conditions")
    merged.add_argument("stems", nargs="*")
    merged.add_argument("--release")
    merged.add_argument("--priority", nargs="+", choices=PRIORITIES)
    merged.add_argument("--since")
    merged.add_argument("--at-least", type=int)
    merged.add_argument("--source")
    merged.add_argument("--unattended", action="store_true")
    sub.add_parser("publish", help="build the tagged release and upload it when release.publish is true")
    release = sub.add_parser("release", help="bump, commit, and tag a local release without publishing")
    part = release.add_mutually_exclusive_group(required=True)
    part.add_argument("--minor", dest="part", action="store_const", const="minor")
    part.add_argument("--patch", dest="part", action="store_const", const="patch")
    sub.add_parser("dismiss", help="dismiss box messages under the lock").add_argument("ids", nargs="+")
    sub.add_parser("covmap", help="build the coverage map")
    covgate = sub.add_parser("covgate", help="check a coverage JSON report against thresholds")
    covgate.add_argument("--gate", type=Path, default=Path("test-gate.toml"))
    covgate.add_argument("--report", type=Path, default=Path("coverage.json"))
    covgate.add_argument("command", nargs=argparse.REMAINDER)
    new = sub.add_parser("new", help="template tickets/<stem>/ticket.md and lint it")
    new.add_argument("stem")
    new.add_argument("--kind", choices=KINDS, default="feature")
    new.add_argument("--evidence", nargs="+", metavar="PATH")
    ordering = sub.add_parser("order", help="edit a ticket's priority or ordering")
    ordering.add_argument("stem")
    ordering.add_argument("--priority", choices=PRIORITIES)
    ordering.add_argument("--runs-before", nargs="*", metavar="STEM")
    run = sub.add_parser("run", help="drive one ticket through intake and the stage pipeline under the lock")
    run.add_argument("stem")
    for verb in ("confirm", "reject"):
        verdict = sub.add_parser(verb, help=f"{verb} a draft or Reject item; publish the verdict to a running serve holding the lock")
        verdict.add_argument("stems", nargs="+")
        verdict.add_argument("--yes", action="store_true")
        verdict.add_argument("--extension", action="store_true")
    dr = sub.add_parser("drain", help="run every eligible ticket to quiescence under the lock")
    dr.add_argument("--detach", action="store_true", help="run in its own session and append to <state_dir>/drain.out")
    dr.add_argument("--parked", action="append", default=[], metavar="STEM", help="a stem the handing-off parent drain parked (set by the self-upgrade re-exec)")
    dr.add_argument("--deadline", type=datetime.fromisoformat, default=None)
    dr.add_argument("--stop-lifecycle", help=argparse.SUPPRESS)
    sub.add_parser("serve", help="run the foreground daemon until kill, stop, or a signal stops it")
    return ap


def main(
    argv: Sequence[str] | None = None,
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    clock: Clock = _clock,
    pipeline: runner.Pipeline = runner.pipeline,
    reexec: ProcessExec | None = None,
    spawn: Callable = seams.spawn_detached,
    terminal: tuple[Callable[[], bool], Callable[[str], str]] | None = None,
) -> int:
    invocation = list(argv) if argv is not None else sys.argv[1:]
    args = _parser().parse_args(invocation)
    repo = Path(cwd) if cwd is not None else Path.cwd()
    env = dict(os.environ) if env is None else env

    # Utilities
    def handle_docs():
        for name, purpose in (
            ("authoring", "ticket authoring"),
            ("running", "host operation"),
            ("contract", "host contract"),
            ("qwen", "local qwen provider setup"),
            ("gemini", "gemini provider setup"),
        ):
            print(f"{Path(clutch.__file__).parent / 'docs' / f'host-{name}.md'}  {purpose}")
        return 0

    def handle_init_config():
        async def init_config():
            exec_ = SubprocessExec()
            statuses = [await cli_status(name, exec_=exec_, env=env, cwd=repo) for name in ADAPTERS]
            listings = {status.name: await ADAPTERS[status.name].list_models(exec_=exec_, env=env, cwd=repo) for status in statuses if status.where != "absent"}
            try:
                return suggest_config(statuses, listings)
            except ValueError:
                raise runner.Refusal("no provider CLI found", f"run: clutch install {'|'.join(sorted(ADAPTERS))}") from None

        text = asyncio.run(init_config())
        load_config_text(text, path=repo / "config.yaml", cwd=repo)
        print(text, end="")
        if args.write:
            try:
                LocalFileSystem().publish(repo / "config.yaml", text.encode())
            except FileExistsError:
                raise runner.Refusal("config.yaml already exists", "remove it, or omit --write and merge the printed suggestion by hand") from None
        return 0

    def handle_install():
        for name in args.providers:
            if name not in ADAPTERS:
                raise runner.Refusal(f"unknown provider {name!r}", f"name one of {', '.join(sorted(ADAPTERS))}")

        async def install():
            exec_ = SubprocessExec()
            for name in args.providers or ADAPTERS:
                if args.providers:
                    package = ADAPTERS[name].PACKAGE
                    try:
                        rc, _, err = await exec_.run(["pnpm", "add", "-D", f"{package}@latest"], cwd=repo, env=tool_env(env, repo), timeout=INSTALL_TIMEOUT_S)
                    except ExecutableNotFound:
                        raise runner.Refusal("pnpm is not on PATH", "install pnpm (https://pnpm.io/installation), then rerun clutch install") from None
                    if rc:
                        lines = [line for line in err.splitlines() if line.strip()]
                        raise runner.Refusal(f"pnpm add {package}@latest failed (rc {rc}): {lines[-1] if lines else ''}", "fix the pnpm error, then rerun clutch install")
                status = await cli_status(name, exec_=exec_, env=env, cwd=repo)
                print(
                    f"{status.name}: {status.where}{' ' + status.version if status.version else ''}, package {status.package}" + (f" -- run: clutch install {name}" if status.where == "absent" else "")
                )
                if name == "qwen":
                    print("ollama: not installed by clutch; follow clutch/docs/host-qwen.md")

        asyncio.run(install())
        return 0

    def handle_migrate_config():
        migrate_config(args.config, cwd=repo, fs=LocalFileSystem())
        return 0

    def handle_covgate():
        from clutch.covgate import run_gate

        if len(args.command) < 2 or args.command[0] != "--":
            return _fail("covgate", "name the unit-test command after --")
        command = args.command[1:]
        # ProcessExec starts a new session, orphaning the test run when Check kills
        # covgate's group on timeout; inheriting the group carries the kill to it.
        try:
            return run_gate(command, gate_path=repo / args.gate, report_path=repo / args.report, run=lambda argv: subprocess.run(argv, cwd=repo, env=env).returncode)
        except FileNotFoundError:
            return _fail("covgate", f"{command[0]} not found -- install it or correct the command after --")

    def handle_doctor():
        from clutch import doctor

        results = asyncio.run(doctor.check(repo=repo, config_path=args.config, env=env, exec_=SubprocessExec(), clock=clock, sleep=asyncio.sleep, in_venv=sys.prefix != sys.base_prefix))
        print(doctor.render(results), end="")
        return 0 if all(r.passed for r in results) else 2

    def handle_issue():
        try:
            body = (repo / args.body).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise runner.Refusal(f"cannot read --body file {args.body}: {exc}", "pass the path of a UTF-8 Markdown file") from None
        try:
            redactor = Redactor.from_config(load_config(args.config, cwd=repo), env)
        except ConfigError as exc:
            print(f"issue: config did not load, so no secrets were scrubbed: {exc}", file=sys.stderr)
            redactor = Redactor({})
        print(issue.link(args.issue_class, args.title, body, redactor.scrub))
        return 0

    def handle_update_config():
        async def update_config():
            suggested = False
            exec_ = SubprocessExec()
            for provider in config.providers:
                name = provider.name
                if name not in ADAPTERS:
                    print(f"{name}: no shipped cli adapter; name one of {', '.join(sorted(ADAPTERS))}")
                    suggested = True
                    continue
                try:
                    listing = await ADAPTERS[name].list_models(exec_=exec_, env=child_env(env, config, provider), cwd=repo)
                except ExecutableNotFound as exc:
                    raise runner.Refusal(str(exc), f"run: clutch install {name}") from None
                print(name)
                served = " ".join(f"{label}={model}" if label != model else model for label, model in listing.models.items())
                print(f"  serves: {served or 'nothing listed'}")
                for problem in listing.problems:
                    print(f"  problem: {problem}")
                configured = [(f"models_by_tier.{tier}", getattr(provider.models_by_tier, tier)) for tier in TIERS]
                configured += [
                    (f"routing[{i}].candidates[{j}].model", candidate.model)
                    for i, route in enumerate(config.routing)
                    for j, candidate in enumerate(route.candidates)
                    if candidate.provider == name and candidate.model is not None
                ]
                for where, model in configured:
                    alias = next((label for label, value in listing.models.items() if label != value and label in model), None)
                    if model in listing.models.values():
                        status = "current"
                    elif alias:
                        status = f"-> {listing.models[alias]} (latest {alias})"
                    elif model == PLACEHOLDER:
                        status = "is the placeholder; pick a served name"
                    elif not listing.models and listing.problems:
                        status = "unverified; no models listed (see problem above)"
                    else:
                        status = "not served; pick a served name"
                    print(f"  {where}: {model} {status}")
                    suggested |= status != "current"
            return int(suggested)

        return asyncio.run(update_config())

    def handle_probe():
        declared = {p.name: p for p in config.providers}
        unknown = set(args.providers) - declared.keys()
        if unknown:
            print(f"unknown providers: {', '.join(sorted(unknown))}; declared providers: {', '.join(declared)}", file=sys.stderr)
            return 2

        async def probe():
            failed = False
            exec_ = SubprocessExec()
            redactor = Redactor.from_config(config, env)
            for name in args.providers or declared:
                provider = declared[name]
                try:
                    if name not in ADAPTERS:
                        raise ProviderSetupError(f"provider {name!r} has no shipped cli adapter; name a provider one of {sorted(ADAPTERS)}")
                    adapter = ADAPTERS[name](
                        provider,
                        config=config,
                        exec_=exec_,
                        fs=LocalFileSystem(),
                        redactor=redactor,
                        env=env,
                        cwd=repo,
                        timeout=PREFLIGHT_TIMEOUT_S,
                    )
                except Exception as exc:
                    print(f"{name}: {exc}")
                    failed = True
                    continue
                seen = set()
                for tier in TIERS:
                    model = getattr(provider.models_by_tier, tier)
                    if model in seen:
                        continue
                    seen.add(model)
                    req = LLMRequest(surface="preflight", rendered=PROBE_PROMPT, tier=tier, effort="low", ticket=None, worktree=None)
                    try:
                        await adapter.invoke(req, model)
                        print(f"{name} {model}: ok")
                    except Exception as exc:
                        road = getattr(exc, "paved_road", None)
                        print(f"{name} {model}: {exc}" + (f" -- {road}" if road else ""))
                        failed = True
            return 1 if failed else 0

        return asyncio.run(probe())

    def handle_core():
        hostfiles.refresh(routed_conduct_paths(config, repo), LocalFileSystem())
        return 0

    def handle_covmap():
        from clutch.covmap import build

        asyncio.run(build(repo=repo, config=config, exec_=exec_, git=checkout.git, fs=checkout.fs, env=child_env(env, config)))
        return 0

    # Projections
    def handle_watch():
        from clutch import observe

        context = _observe_context(repo, config, args.config, exec_, checkout.git, env)
        if args.verb == "snapshot":
            print(json.dumps(observe.snapshot(context)))
        elif args.once:
            print(observe.text_snapshot(context))
        else:
            try:
                while True:
                    print("\033[2J\033[H" + observe.text_snapshot(context), flush=True)
                    time.sleep(3)
            except KeyboardInterrupt:
                pass
        return 0

    def handle_stats():
        from clutch.stats import render_stats, stats_tree, window_start

        events = checkout.journal.read()
        now = checkout.clock()
        try:
            window_start(events, now, args.window)
        except ValueError as exc:
            return _fail("stats", str(exc))
        result = asyncio.run(_stats(checkout, events, now, args.window))
        print(json.dumps(stats_tree(result) if args.tree else result) if args.tree or args.json else render_stats(result), end="\n" if args.tree or args.json else "")
        return 0

    def handle_status():
        print(render(asyncio.run(_status(checkout))), end="")
        return 0

    # Authoring
    def handle_new():
        return _new(repo, args.stem, args.kind, args.evidence or ())

    def handle_prompt():
        if args.kind in ("drain-loop", "plan-ticket-drain"):
            if args.stems:
                raise runner.Refusal(f"{args.kind} takes no stem", f"run clutch prompt {args.kind} with no stems")
            print(ask.render(args.kind, "", config, repo), end="")
            return 0
        if args.kind == "drafts":
            if args.stems:
                raise runner.Refusal("drafts prompt takes no stems", "run clutch prompt drafts with no stems")
            from clutch import observe

            exec_ = SubprocessExec()
            git = Git(exec_, env={**child_env(env, config), "GIT_OPTIONAL_LOCKS": "0"}, timeout=GIT_TIMEOUT_S, commit_lock=CommitLock(config.state_dir, clock=clock, sleep=asyncio.sleep))
            context = _observe_context(repo, config, args.config, exec_, git, env)
            stems = [row["stem"] for row in observe.snapshot(context)["rows"] if row["draft"]]
            if not stems:
                raise runner.Refusal("no draft tickets await confirm or reject", "run triage, or author a ticket with clutch new")
            print(ask.render("drafts", stems, config, repo), end="")
            return 0
        if args.kind == "box":
            if not args.stems:
                raise runner.Refusal("box prompt requires ids", "name at least one box id")
            print(ask.render("box", args.stems, config, repo), end="")
            return 0
        if len(args.stems) != 1:
            raise runner.Refusal("ticket prompt requires exactly one stem", "name one ticket stem")
        args.stem = args.stems[0]
        if findings := stem_findings(args.stem):
            raise runner.Refusal(findings[0].message, findings[0].paved_road)
        if args.kind != "author" and not (repo / ticket_path(args.stem)).is_file():
            raise runner.Refusal(f"{ticket_path(args.stem)} does not exist", f"author it with clutch new {args.stem}")
        from clutch import observe

        events = observe.journal(config.state_dir)
        last = {e["ticket"]: {**e["body"], "ts": e["ts"]} for e in events if e.get("type") == "state_transition" and e.get("ticket")}
        kind = "running" if args.kind == "diagnose" and args.stem in observe.running_stems(config.state_dir, last) else args.kind
        print(ask.render(kind, args.stem, config, repo), end="")
        return 0

    def handle_suggest():
        if not args.summary.strip():
            raise runner.Refusal("blank summary", "pass the idea as one quoted argument")
        from clutch.box import Box, RereportJournal

        box = Box(config.state_dir / "box", checkout.fs, rereport=RereportJournal(checkout.journal))
        id, created = box.enqueue(message_class="suggestion", origin="session", summary=args.summary, occurrence_id=uuid4().hex)
        print(f"suggest: filed {id}" if created else f"suggest: already in the box as {id}")
        return 0

    def handle_lint():
        return asyncio.run(_lint(checkout, args.stems))

    def handle_order():
        return _order(checkout, args.stem, args.priority, args.runs_before)

    def handle_review():
        for stem in args.stems:
            if result := asyncio.run(_review(checkout, stem)):
                return result
        return 0

    # Control
    def handle_control():
        return asyncio.run(_control(checkout, args.verb))

    def handle_verdict():
        for stem in args.stems:
            if result := asyncio.run(_verdict(checkout, stem, args.verb, read_input, args.yes, args.extension)):
                return result
        return 0

    # Lock holders
    def handle_roadmap():
        from clutch import roadmap

        if args.roadmap_verb == "status":
            print("\n".join(asyncio.run(roadmap.status(checkout))))
            return 0
        if args.roadmap_verb == "gate":
            ok, lines = asyncio.run(roadmap.run_gate(checkout, args.release))
            print("\n".join(lines))
            return 0 if ok else 1
        if args.roadmap_verb == "accept":
            from clutch import acceptance
            from clutch.driver import Driver

            async def accept_release():
                session = build_control(checkout).providers
                try:
                    llm = await _preflighted_llm(checkout, session)
                    driver = Driver.from_config(config, journal=checkout.journal, llm=llm, env=env, clock=clock, sleep=checkout.sleep, fs=checkout.fs)
                    return await acceptance.accept(checkout, driver, args.release)
                finally:
                    await session.close()

            ok, lines = asyncio.run(accept_release())
            print("\n".join(lines))
            return 0 if ok else 1
        if args.roadmap_verb == "merged":
            ok, lines = asyncio.run(
                roadmap.merged(checkout, args.stems, release=args.release, priorities=args.priority or (), since=args.since, at_least=args.at_least, source=args.source, unattended=args.unattended)
            )
            print("\n".join(lines))
            return 0 if ok else 1
        if args.ahead < 1:
            raise runner.Refusal("--ahead must be at least 1", "choose a positive window")

        async def roadmap_pass():
            async with _locked(config.state_dir, "roadmap", instance_id=await checkout.git.describe(repo), clock=clock):
                await runner.reap(checkout)
                session = build_control(checkout).providers
                try:

                    async def author_messages(ids):
                        llm = await _preflighted_llm(checkout, session)
                        await triage.triage_pass(checkout, llm, frozenset(ids))

                    return await roadmap.author_ahead(checkout, args.ahead, author_messages)
                finally:
                    await session.close()

        print("\n".join(asyncio.run(roadmap_pass())))
        return 0

    def handle_release():
        from clutch import release

        async def release_version():
            async with _locked(config.state_dir, "release", instance_id=await checkout.git.describe(repo), clock=clock):
                version, sha = await release.release(repo, checkout.git, checkout.exec_, child_env(env, config), args.part)
                release.journal_release(checkout.journal, version, sha)
                return version, sha

        version, sha = asyncio.run(release_version())
        print(f"release: tagged v{version} at {sha}")
        return 0

    def handle_publish():
        from clutch import release

        async def publish_version():
            async with _locked(config.state_dir, "publish", instance_id=await checkout.git.describe(repo), clock=clock):
                return await release.publish(repo, checkout.git, checkout.exec_, checkout.fs, env, config)

        version, artifacts, uploaded = asyncio.run(publish_version())
        for artifact in artifacts:
            print(f"publish: built {artifact}")
        print(f"publish: uploaded {version} to PyPI" if uploaded else "publish: release.publish is false; uploaded nothing -- set release.publish: true in config.yaml to upload")
        return 0

    def handle_dismiss():
        async def dismiss_messages():
            async with _locked(config.state_dir, "dismiss", instance_id=await checkout.git.describe(repo), clock=clock):
                await runner.reap(checkout)
                return await triage.dismiss(checkout, args.ids)

        print("\n".join(asyncio.run(dismiss_messages())))
        return 0

    def handle_triage():
        async def one_pass() -> list[tuple[str, str]]:
            async with _locked(config.state_dir, "triage", instance_id=await checkout.git.describe(repo), clock=clock):
                await runner.reap(checkout)
                session = build_control(checkout).providers
                try:
                    triage.validate_ids(checkout, args.ids)
                    llm = await _preflighted_llm(checkout, session)
                    return await triage.triage_pass(checkout, llm, frozenset(args.ids))
                finally:
                    await session.close()

        lines = asyncio.run(one_pass())
        print("\n".join(line for _, line in lines) if lines else "no pending suggestions")
        return 0

    def handle_serve():
        return asyncio.run(serve.serve(checkout, config_path=args.config, signals=_engine_signals, argv=invocation, reexec=reexec or SubprocessExec()))

    def handle_retro():
        return asyncio.run(_retro(checkout, pipeline, config_path=args.config))

    def handle_detach():
        output = config.state_dir / "drain.out"
        pid = spawn([sys.executable, "-m", "clutch", *(["--config", str(args.config)] if args.config else []), "drain"], cwd=repo, env=env, output=output)
        print(f"drain: pid {pid}, output {output}")
        return 0

    def handle_pipeline():
        nonlocal checkout
        checkout = replace(checkout, control=build_control(checkout))
        checkout.control.load_config = _config_reloader(args.config, repo)
        dispatch = pipeline(checkout)
        if args.verb == "drain":
            from clutch.retro import Retro

            class DrainDispatch:
                _retro = Retro(checkout, dispatch)
                _driver = staticmethod(build_driver())

                async def __call__(self, ticket):
                    return await dispatch(ticket)

                def __getattr__(self, name):
                    return getattr(dispatch, name)

            # The handoff uses its own process seam.
            report = asyncio.run(
                drain.drain(
                    checkout,
                    DrainDispatch(),
                    signals=_engine_signals,
                    reexec=reexec or SubprocessExec(),
                    parked=args.parked,
                    deadline=args.deadline,
                    stop_lifecycle=args.stop_lifecycle,
                    argv=(["--config", str(args.config)] if args.config else []) + ["drain"],
                )
            )
            if report.handoff is None:
                print(report.render(), end="")
            return report.exit_code
        return asyncio.run(runner.run_ticket(args.stem, checkout, dispatch))

    handlers = {
        "docs": handle_docs,
        "init-config": handle_init_config,
        "install": handle_install,
        "migrate-config": handle_migrate_config,
        "covgate": handle_covgate,
        "new": handle_new,
        "doctor": handle_doctor,
        "issue": handle_issue,
        "update-config": handle_update_config,
        "probe": handle_probe,
        "core": handle_core,
        "prompt": handle_prompt,
        "suggest": handle_suggest,
        "covmap": handle_covmap,
        "snapshot": handle_watch,
        "watch": handle_watch,
        "stats": handle_stats,
        "lint": handle_lint,
        "order": handle_order,
        "status": handle_status,
        "kill": handle_control,
        "pause": handle_control,
        "resume": handle_control,
        "stop": handle_control,
        "reject": handle_verdict,
        "confirm": handle_verdict,
        "review": handle_review,
        "roadmap": handle_roadmap,
        "release": handle_release,
        "publish": handle_publish,
        "dismiss": handle_dismiss,
        "triage": handle_triage,
        "serve": handle_serve,
        "retro": handle_retro,
        "run": handle_pipeline,
        "drain": handle_pipeline,
    }

    try:
        if args.verb in {"confirm", "reject"}:
            isatty, read_input = terminal if terminal is not None else (sys.stdin.isatty, input)
            if not (args.yes or args.extension) and not isatty():
                raise runner.Refusal("verdict requires an interactive terminal", "a human runs this in a terminal: `clutch confirm|reject <stem>`")
        if args.verb in {"docs", "init-config", "install", "migrate-config", "covgate", "new", "doctor", "issue"}:
            return handlers[args.verb]()
        config = load_config(args.config, cwd=repo)
        if args.verb == "drain" and args.detach:
            return handle_detach()
        if args.verb in {"update-config", "probe", "core", "prompt"}:
            return handlers[args.verb]()
        exec_ = SubprocessExec()
        checkout = runner.Checkout(
            repo=repo,
            config=config,
            env=env,
            exec_=exec_,
            git=Git(
                exec_,
                env={**child_env(env, config), **({"GIT_OPTIONAL_LOCKS": "0"} if args.verb in {"lint", "watch", "snapshot"} else {})},
                timeout=GIT_TIMEOUT_S,
                commit_lock=CommitLock(config.state_dir, clock=clock, sleep=asyncio.sleep),
            ),
            journal=Journal(config.state_dir, clock),
            fs=LocalFileSystem(),
            clock=clock,
        )
        if args.verb in {"serve", "drain", "run"}:
            messages = asyncio.run(hostfiles.stale_core(repo, config, checkout.git))
            if messages:
                raise runner.Refusal("; ".join(messages), f"run clutch core, then commit the conduct files and retry {args.verb}")
        return handlers[args.verb]()
    except UnknownBoxId as e:
        return _fail(args.verb, f"{e} -- name ids that clutch status lists")
    except (ConfigError, runner.Refusal, LockHeld, CommitLockTimeout, IntakeRefused, JournalCorruption, ProviderSetupError, ExecutableNotFound, hostfiles.MarkerCorruption) as e:
        road = f" -- repair the selected config and retry {args.verb}" if args.verb in {"retro", "covmap"} and isinstance(e, ConfigError) else ""
        return _fail(args.verb, f"{e}{road}")


async def _review(checkout: runner.Checkout, stem: str) -> int:
    from clutch.driver import Driver
    from clutch.tickets import intake

    # Preserve stem, intake, existence and settled refusal precedence before reading main.
    admission = review_admission(stem, (), True, None)
    if admission.outcome == "refuse":
        raise runner.Refusal(admission.message, admission.paved_road)
    pending = await runner.ticket_pending(checkout.git, checkout.repo, stem)
    result = await intake(checkout.repo, checkout.git, checkout.journal, checkout.fs, stems={stem}) if pending else None
    path = checkout.repo / ticket_path(stem)
    intake_decision = result.refused.get(stem) if result else None
    history = checkout.journal.read() if path.is_file() and not intake_decision else ()
    states = last_states(history)
    admission = review_admission(stem, history, path.is_file(), None, intake_decision, pending=pending)
    if admission.outcome == "refuse":
        raise runner.Refusal(admission.message, admission.paved_road)
    text = await checkout.git._run(checkout.repo, "show", f"main:{ticket_path(stem)}")
    try:
        ticket = validate_ticket(stem, text, checkout.repo)
    except TicketInvalid as exc:
        ticket = exc.findings
    admission = review_admission(stem, history, True, ticket, pending=pending)
    if admission.outcome == "refuse":
        raise runner.Refusal(admission.message, admission.paved_road)
    unmerged = [dep for dep in ticket.depends if states.get(dep) != "merged"]
    session = build_control(checkout).providers
    try:
        llm = await _preflighted_llm(checkout, session)
        driver = Driver.from_config(checkout.config, journal=checkout.journal, llm=llm, env=checkout.env, clock=checkout.clock, sleep=checkout.sleep, fs=checkout.fs)
        verdict = await requisition.review_ticket(
            driver,
            repo=checkout.repo,
            stem=stem,
            text=text,
            specs_dir=runner.SPECS_DIR,
            coverage_map=checkout.config.state_dir / "coverage-map.json" if checkout.config.review.coverage_map is not None else None,
            tier=checkout.config.routing_default_tier,
            stem_slot=f"review-{stem}",
            run_seq=len(history),
            attempt=0,
            call_seq=1,
            expected_budget="surface",
            prior=await requisition.prior_review(checkout.git, checkout.repo, history, stem, text),
        )
    finally:
        await session.close()
    if unmerged:
        print(f"review {stem}: provisional, not recorded -- depends on unmerged {', '.join(unmerged)}; the drain reviews it again before its first run")
    else:
        # A journaled approval would let the drain skip its review.
        checkout.journal.append(
            EventType.SIGNAL,
            {
                "signal": "requisition_verdict",
                "verdict": verdict.verdict,
                "findings": [{"code": f.code, "message": f.message} for f in verdict.findings],
                "ticket_sha": verdict.ticket_sha,
                "provider": verdict.provider,
                "model": verdict.model,
                "spec_version": verdict.spec_version,
            },
            ticket=stem,
        )
    print(f"review {stem}: {verdict.verdict} -- {verdict.summary}")
    for finding in verdict.findings:
        location = f" {finding.path}:{finding.line}" if finding.path and finding.line is not None else f" {finding.path}" if finding.path else ""
        print(f"- [{finding.code}]{location} {finding.message} ({finding.paved_road})")
    return 0 if verdict.verdict == "approve" else 1


def _require_engine(exc: LockHeld) -> None:
    verb = (exc.holder or {}).get("verb") or "unknown holder"
    if verb not in ENGINE_VERBS:
        raise runner.Refusal(f"writer lock held by {verb}", f"wait for {verb} to finish, then retry") from None


async def _submit_engine(checkout, exc, verb, *, stem=None, extension=False):
    _require_engine(exc)
    if stem is not None and await runner.ticket_pending(checkout.git, checkout.repo, stem):
        from clutch.tickets import intake

        result = await intake(checkout.repo, checkout.git, checkout.journal, checkout.fs, stems={stem})
        if refused := result.refused.get(stem):
            raise runner.Refusal(f"{ticket_path(stem)} failed intake: " + "; ".join(f.message for f in refused), "fix the ticket and retry the verdict")
    try:
        lifecycle, hold = control.read_active(checkout.config.state_dir, Path.read_bytes)
    except ValueError as exc:
        raise runner.Refusal("current control identity unavailable", str(exc)) from exc
    if stem is not None:
        request = control.AdmissionRequest(uuid4().hex, lifecycle, verb, stem, None, "extension" if extension else "operator")
    else:
        if verb == "resume" and hold is None:
            raise runner.Refusal("no current hold identity", "read the running engine's current control identity and submit a new request")
        request = control.ControlRequest(uuid4().hex, lifecycle, verb, hold if verb == "resume" else None)
    control.publish_request(checkout.config.state_dir, request, checkout.fs)
    return request


async def _retro(checkout, pipeline, *, config_path=None):
    from clutch.retro import Retro, RetroConstructionError, measurements, project_window, suppressing_failure

    async with AsyncExitStack() as stack:
        try:
            await stack.enter_async_context(_locked(checkout.config.state_dir, "retro", instance_id=await checkout.git.describe(checkout.repo), clock=checkout.clock))
        except LockHeld as exc:
            request = await _submit_engine(checkout, exc, "retro")
            print(f"retro submitted: {request.request_id}; the running engine runs it between tickets")
            return 0
        try:
            await runner.reap(checkout)
            checkout = replace(checkout, control=build_control(checkout))
            checkout.control.load_config = _config_reloader(config_path, checkout.repo)
            dispatch = pipeline(checkout)
            try:
                window = project_window(checkout.journal.read())
            except JournalCorruption as exc:
                raise runner.Refusal(str(exc), "restore journal readability from backup and retry retro") from None
            selected = bool(measurements(window)["merged_count"])
            suppressed = suppressing_failure(window) is not None
            if selected and not suppressed and hasattr(dispatch, "prepare"):
                await dispatch.prepare()
            try:
                result = await Retro(checkout, dispatch)(forced=True)
            except RetroConstructionError as exc:
                raise runner.Refusal("retro Driver unavailable", str(exc)) from None
            if not selected:
                print("retro: no merge since the latest completed report")
                return 0
            if result is not None:
                print(f"retro: committed tickets/retro/{window.sequence:06d}.md")
                return 0
            print("retro: no report committed; inspect status and the Suggestion Box")
            return 1
        finally:
            if checkout.control is not None:
                await checkout.control.providers.close()


def stuck_ceiling_finding(stuck_minutes: int, ceiling: int) -> str | None:
    if stuck_minutes > ceiling:
        return f"`## Time budget` stuck {stuck_minutes}m exceeds drain.max_ticket_minutes ({ceiling}m); lower `- stuck:` to at most {ceiling}m or split the ticket"
    return None


async def _lint(checkout: runner.Checkout, stems: Sequence[str]) -> int:
    root = checkout.repo / "tickets"
    valid = total = 0
    exit_code = 0
    try:
        entries = list(root.iterdir())  # Unlike glob, unreadable directories must refuse.
        selected = list(dict.fromkeys(stems)) if stems else sorted(p.name for p in entries if (p / "ticket.md").is_file())
        common_dir = await checkout.git.git_common_dir(checkout.repo)
        repo = checkout.repo.resolve()
        state_dir = checkout.config.state_dir.resolve()
        journal = checkout.journal
        if common_dir.parent != repo and state_dir.is_relative_to(repo):
            journal = Journal(common_dir.parent / state_dir.relative_to(repo), checkout.clock)
        events = journal.read()
        pending = _pending(checkout.repo, _porcelain(await checkout.git.status_porcelain(checkout.repo)))
        for stem in selected:
            rel = ticket_path(stem)
            path = checkout.repo / rel
            # Check existence before the stem grammar, without following an escaped path.
            inside = Path(stem).name == stem and stem not in {".", ".."} and path.resolve().is_relative_to(root.resolve())
            admission = lint_admission(stem, events, inside and path.is_file())
            if admission.outcome == "refuse":
                print(f"{rel}: {admission.message} ({admission.paved_road})")
                total += 1
                exit_code = 2
                continue
            if admission.outcome == "noop":
                continue
            total += 1
            text, findings = _intake_claims(stem, path.read_text(), pending.get(stem, False))
            ceiling_finding = None
            try:
                if findings:
                    raise TicketInvalid(findings)
                ticket = validate_ticket(stem, text, checkout.repo)
                ceiling_finding = stuck_ceiling_finding(ticket.stuck_minutes, checkout.config.drain.max_ticket_minutes)
                paths = await checkout.git._run(checkout.repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", f"tickets/{stem}/evidence/")
                findings = lint_findings(ticket, checkout.repo) + evidence_findings(ticket, checkout.repo, paths=paths.split("\0"))
            except TicketInvalid as exc:
                findings = exc.findings
            for finding in findings:
                message = " ".join(finding.message.splitlines())
                road = " ".join(finding.paved_road.splitlines())
                print(f"{finding.path or rel}: {message} ({road})")
            if ceiling_finding:
                print(f"{rel}: {ceiling_finding}")
            if findings or ceiling_finding:
                exit_code = max(exit_code, 1)
            else:
                valid += 1
    except (OSError, UnicodeError, GitError) as exc:
        print(f"{root}: {exc} (restore ticket and repository readability, then retry clutch lint)")
        exit_code = 2
    print(f"lint: {valid}/{total} tickets valid")
    return exit_code


async def _stats(checkout, events, now, window):
    from clutch.stages import Invoice
    from clutch.stats import project_stats, window_start

    start = window_start(events, now, window)
    kinds = {}
    for stem in {e.ticket for e in events if e.ticket}:
        try:
            split = split_frontmatter((checkout.repo / ticket_path(stem)).read_text())
            data = yaml.safe_load(split[0]) if split else None
            if isinstance(data, dict) and data.get("kind") in KINDS:
                kinds[stem] = data["kind"]
        except OSError, UnicodeError, yaml.YAMLError:
            pass
    checks = {}
    for e in events:
        if e.type == EventType.EFFECT_COMPLETION and e.ticket and re.fullmatch(r"ticket-plane/[^/]+/\d+/checks", e.key or "") and start <= datetime.fromisoformat(e.ts) <= now:
            text = await checkout.git._run(checkout.repo, "show", f"{e.body['result']['commit']}:tickets/{e.ticket}/checks.json")
            checks[e.key] = Invoice.model_validate_json(text)
    return project_stats(events, kinds, checks, now=now, window=window)


async def _status(checkout: runner.Checkout):
    from clutch.box import BOX_DIR, Box, RereportJournal
    from clutch.retro import production_evidence, project_window
    from clutch.specs import load_spec

    events = checkout.journal.read()
    window = project_window(events)
    await production_evidence(window, checkout)
    spec = load_spec((runner.SPECS_DIR / "retro.md").read_text())
    provenance = {"head": await checkout.git.rev_parse(checkout.repo, "HEAD"), "spec_version": spec.meta.version, "at": checkout.clock().isoformat()}
    return project(
        events,
        alive=observe.lock_holder(checkout.config.state_dir) is not None,
        window=window,
        provenance=provenance,
        box=Box(checkout.config.state_dir / BOX_DIR, checkout.fs, rereport=RereportJournal(checkout.journal)),
        policy=checkout.config.box_policy,
    )


def _engine_signals(stop: Callable[[], None]) -> Callable[[], None]:
    """Real signal delivery is composed here, alongside the other operating-system seams."""
    loop = asyncio.get_running_loop()
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    for sig in previous:
        loop.add_signal_handler(sig, stop)

    def restore() -> None:
        for sig, handler in previous.items():
            loop.remove_signal_handler(sig)
            signal.signal(sig, handler)

    return restore


async def _control(checkout: runner.Checkout, verb: str) -> int:
    async with AsyncExitStack() as stack:
        try:
            await stack.enter_async_context(_locked(checkout.config.state_dir, verb, instance_id=await checkout.git.describe(checkout.repo), clock=checkout.clock))
        except LockHeld as exc:
            request = await _submit_engine(checkout, exc, verb)
            print(f"{verb} submitted: {request.request_id}")
        else:
            if verb == "kill":
                raise runner.Refusal("nothing running to kill", "start a drain before submitting kill")
            if verb == "stop":
                raise runner.Refusal("nothing running to stop", "start a drain or serve before submitting stop")
            print(f"nothing running to {verb}")
    return 0


async def _verdict(checkout, stem, verb, read_input, yes, extension):
    if findings := stem_findings(stem):
        raise runner.Refusal(findings[0].message, findings[0].paved_road)
    history = checkout.journal.read()
    queued = reject_queue(history).get(stem)
    path = checkout.repo / ticket_path(stem)
    if queued is not None:
        preview = f"Reject queue: {queued.get('to', 'unknown')} -- {queued.get('reason', 'reason unavailable')}"
    elif path.is_file():
        split = split_frontmatter(path.read_text())
        data, errors = _load_frontmatter(split[0], str(path)) if split else (None, [True])
        if errors:
            raise runner.Refusal(f"{ticket_path(stem)} has invalid frontmatter", "fix the ticket and retry the verdict")
        preview = f"ticket state: {data.get('state', 'unknown')}"
    else:
        preview = "no ticket file"
    print(f"{stem}: {preview}")
    try:
        answer = "y" if yes or extension else read_input(f"{verb} {stem}? [y/N] ")
    except EOFError:
        answer = ""
    if answer.strip().lower() not in {"y", "yes"}:
        print("verdict aborted")
        return 1
    try:
        return await runner.verdict(stem, checkout, kill=verb == "reject", extension=extension)
    except LockHeld as exc:
        request = await _submit_engine(checkout, exc, verb, stem=stem, extension=extension)
    print(f"{verb} submitted: {request.request_id} -- `clutch status` shows the outcome")
    return 0


def _order(checkout, stem, priority, runs_before):
    if findings := stem_findings(stem):
        raise runner.Refusal(findings[0].message, findings[0].paved_road)
    if priority is None and runs_before is None:
        raise runner.Refusal("no ordering option supplied", "supply --priority or --runs-before")
    path = checkout.repo / ticket_path(stem)
    exists = path.is_file()
    events = checkout.journal.read() if exists else ()
    state = last_states(events).get(stem)
    holder = observe.lock_holder(checkout.config.state_dir) if state == "running" and stem in reconcile.orphans(events) else None
    admission = order_admission(stem, events, exists, holder)
    if admission.outcome == "refuse":
        raise runner.Refusal(admission.message, admission.paved_road)
    text = path.read_bytes().decode()
    try:
        try:
            changed = order(text, priority=priority, runs_before=runs_before)
        except ValueError, StopIteration:
            validate_ticket(stem, text, checkout.repo)
            raise runner.Refusal("ticket ordering fields cannot be edited", "use ordinary priority and section headings, then retry order") from None
        ticket = validate_ticket(stem, changed, checkout.repo)
        if priority is not None and ticket.frontmatter.priority != priority:
            raise runner.Refusal("priority line cannot be edited", "write priority as a plain `priority: P2` line, then retry order")
    except TicketInvalid as exc:
        admission = order_admission(stem, events, exists, holder, exc.findings)
        raise runner.Refusal(admission.message, admission.paved_road) from None
    checkout.fs.write(path, changed.encode())
    fields = ([f"priority: {priority}"] if priority is not None else []) + ([f"runs before: {', '.join(runs_before) or '(cleared)'}"] if runs_before is not None else [])
    print(f"ordered {stem}: {'; '.join(fields)}")
    return 0


def _new(repo: Path, stem: str, kind: str = "feature", evidence: Sequence[str] = ()) -> int:
    """Author a ticket and its evidence outside the lock fence."""
    if kind == "bug" and not evidence:
        raise runner.Refusal(
            "a bug ticket needs its evidence first", f"save the observed failure (output, log excerpt, or captured command output) to a file, then rerun new {stem} --kind bug --evidence <file>"
        )
    if kind != "bug" and evidence:
        raise runner.Refusal("evidence is for bug tickets", "omit --evidence or choose --kind bug")
    sources = [repo / path for path in evidence]
    for source in sources:
        if source.is_symlink() or not source.is_file():
            raise runner.Refusal(f"invalid evidence file: {source}", "supply an existing regular file that is not a symlink")
    if len({source.name for source in sources}) != len(sources):
        raise runner.Refusal("evidence files have duplicate names", "supply files with distinct names")
    if findings := stem_findings(stem):
        raise runner.Refusal(findings[0].message, findings[0].paved_road)
    rel = ticket_path(stem)
    guide = Path(clutch.__file__).parent / "docs" / "host-authoring.md"
    if (repo / rel).exists():
        raise runner.Refusal(f"{rel} already exists", f"read {guide}, then edit it in place, or pick a new stem")
    text = template(kind)
    fs = LocalFileSystem()
    fs.write(repo / rel, text.encode())
    for source in sources:
        fs.write(repo / "tickets" / stem / "evidence" / source.name, source.read_bytes())
    print(f"authored {rel}")
    print(f"read the ticket authoring guide before filling sections: {guide}")
    findings = []
    try:
        ticket = validate_ticket(stem, text, repo)
        findings = lint_findings(ticket, repo)
    except TicketInvalid as e:
        findings = e.findings
        if kind == "bug":
            findings += missing_evidence_findings(stem, repo)
    if findings:
        print(f"fill these before `run {stem}`:")
        for f in findings:
            print(f"- {f.message} ({f.paved_road})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
