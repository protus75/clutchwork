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
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import duckdb

import clutch
from clutch import ask, context, control, drain, hostfiles, index, issue, observe, requisition, runner, seams, serve, tickets, triage
from clutch.box import BOX_DIR, Box, UnknownBoxId
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
from clutch.status import admission_facts, latest_transitions, lint_admission, order_admission, overdue, project, reject_queue, render, review_admission
from clutch.storm import StormLedger
from clutch.tickets import (
    CHECKS_FILE,
    KINDS,
    PRIORITIES,
    IntakeRefused,
    Ticket,
    TicketInvalid,
    _intake_claims,
    _load_frontmatter,
    _pending,
    _porcelain,
    artifact_path,
    evidence_findings,
    lint_findings,
    missing_evidence_findings,
    order,
    read_tolerant,
    split_frontmatter,
    stem_findings,
    template,
    ticket_path,
    validate_ticket,
)
from clutch.timers import Timers

GIT_TIMEOUT_S = 30.0

INDEX_FINDING_EXITS = {"db_open_failed": 2, "git_failed": 1, "embed_failed": 1, "call_unreadable": 1, "box_unreadable": 1, "vss unavailable": 1, "fts unavailable": 1}


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
    problems = await session.preflight_once(checkout.config, llm, llm.preflight) if session.active else []
    if problems:
        raise ProviderSetupError("; ".join(problems))
    return llm


def build_control(checkout: runner.Checkout) -> PauseConsumer:
    """Compose without reading requests, publishing discovery, or starting tasks."""
    from clutch.daemon import storm_producer_for_config

    box = storm_producer_for_config(checkout.config, fs=checkout.fs, journal=checkout.journal, clock=checkout.clock)
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


def _admission_max_runs(parallel):
    return parallel.max_runs if parallel.enabled else 1


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
    log: Callable[..., None] | None = None,
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
        ticket_sha=lambda stem: checkout.git.rev_parse(checkout.repo, f"HEAD:{ticket_path(stem)}"),
        clock=checkout.clock,
        sleep=checkout.sleep,
        debounce=debounce,
        quarantined=quarantined,
        drought_parked=drought_parked,
        completed_unmerged=completed_unmerged,
        max_unmerged=checkout.config.scheduler.max_unmerged,
        max_runs=_admission_max_runs(checkout.config.scheduler.parallel),
        before_dispatch=consumer.checkpoint,
        control=consumer,
        log=log,
    )
    timers = consumer.providers.timers
    restart = Restart(checkout, timers=timers, owned=lambda: core.admission.occupied())
    core.admission.restart = restart
    core.admission._before_dispatch = StartupBoundary(restart, consumer).checkpoint

    def provider_holds():
        held = set(drought_parked())
        for stem, event in latest_transitions(checkout.journal.read()).items():
            if route := event.body.get("provider_drought"):
                snapshot = load_config(config_path, cwd=checkout.repo)
                if consumer.providers.drought(snapshot, route["tier"], route["surface"]):
                    held.add(stem)
        return held

    core.scheduler.flake_fixes = lambda: drain.flake_fixes(Box(checkout.config.state_dir / BOX_DIR, checkout.fs).messages())
    core.scheduler.drought_parked = provider_holds
    return core


def build_serve(
    checkout: runner.Checkout, *, config_path=None, read=None, stems=None, prepare=runner.prepare_pipeline, signals=None, failure=None, argv=("engine", "serve"), reexec=None
) -> serve.Serve:
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


def _command(subparsers, name, *, summary, does, reads, writes, lock, exits, examples):
    return subparsers.add_parser(
        name,
        help=summary,
        description=f"{does}\n\nReads: {reads}\nWrites: {writes}\nLock: {lock}\nExit codes: {exits}",
        epilog="Examples:\n" + "\n".join(f"{example}\n  {does}" for example in examples),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def _subparsers(parser):
    return next((a for a in parser._actions if isinstance(a, argparse._SubParsersAction)), None)


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="clutch", usage="%(prog)s [-h] [--config CONFIG] <command> ...", description="Host guides: clutch host docs")
    ap.add_argument("--config", type=Path, help="config path (default: config.yaml at the checkout root)")
    sub = ap.add_subparsers(dest="verb", required=True, metavar="<command>")
    view = sub.add_parser(
        "view",
        help="show read-only engine views",
        description="Show read-only views of engine state.",
        epilog="Examples:\nclutch view status\n  Show the journal projection.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    view_sub = view.add_subparsers(dest="view_verb", required=True)
    watch = _command(
        view_sub,
        "watch",
        summary="read-only live engine view",
        does="Print a live text view of configured host state, refreshing every three seconds until Ctrl-C; --once prints one view.",
        reads="Config, journal, engine log, tickets, git state and process list.",
        writes="Nothing.",
        lock="None; works while an engine holds the writer lock.",
        exits="0 when stopped or printed; 2 on refusal.",
        examples=["clutch view watch", "clutch view watch --once"],
    )
    watch.add_argument("--once", action="store_true")
    snapshot = _command(
        view_sub,
        "snapshot",
        summary="read-only JSON snapshot",
        does="Print the extension snapshot as JSON, capped by snapshot_merged_limit (default 100); --all-merged includes all settled tickets.",
        reads="Config, journal, journal cache, engine log, lockfiles, box, tickets and git state.",
        writes="Updates the rebuildable journal cache under the state directory.",
        lock="None.",
        exits="0 when printed; 2 on refusal.",
        examples=["clutch view snapshot", "clutch view snapshot --all-merged"],
    )
    snapshot.add_argument("--all-merged", action="store_true", help="Include all merged history.")
    status_parser = _command(
        view_sub,
        "status",
        summary="project current state from the journal (read-only)",
        does="Print the journal projection of section 10.3, including overdue retro and calibration reminders; these run only when invoked; --short omits resolved Suggestion Box history, tombstones and the scorecard.",
        reads="Config, journal, box, retro spec, HEAD and committed checks records.",
        writes="Nothing.",
        lock="None.",
        exits="0 when printed; 2 on refusal.",
        examples=["clutch view status", "clutch view status --short"],
    )
    status_parser.add_argument("--short", action="store_true", help="Omit resolved Suggestion Box entries, tombstones and scorecard.")
    stats = _command(
        view_sub,
        "stats",
        summary="project journal health over a window (read-only)",
        does="Print a health and efficiency projection over a time or ticket window; --json prints JSON and --tree the extension's tree.",
        reads="Config, journal, tickets and committed checks records.",
        writes="Nothing.",
        lock="None.",
        exits="0 when printed; 2 on refusal (a bad window).",
        examples=["clutch view stats", "clutch view stats --window 3d --json"],
    )
    stats.add_argument("--window", default="7d")
    stats.add_argument("--json", action="store_true")
    stats.add_argument("--tree", action="store_true")
    event_parser = _command(
        view_sub,
        "events",
        summary="stream or wait once for actionable engine changes",
        does="Stream changes after a silent baseline; --once returns JSON, optionally resuming with --cursor and waiting up to --timeout seconds.",
        reads="Config, journal, engine log and clutch lockfile.",
        writes="Nothing.",
        lock="None; works while an engine holds the writer lock.",
        exits="0 on completion or Ctrl-C; 2 on invalid options or cursor.",
        examples=["clutch view events", "clutch view events --once --timeout 300"],
    )
    event_parser.add_argument("--once", action="store_true")
    event_parser.add_argument("--cursor", default=None)
    event_parser.add_argument("--timeout", type=float, default=None)
    host = sub.add_parser(
        "host",
        help="check and set up the host checkout",
        description="Check host setup, refresh managed conduct and locate host guides.",
        epilog="Examples:\nclutch host doctor\n  Inspect host setup.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    host_sub = host.add_subparsers(dest="host_verb", required=True)
    _command(
        host_sub,
        "core",
        summary="refresh managed conduct in every routed agent's root file",
        does="Insert or refresh the managed clutch:core block in each routed conduct file, inspecting every file before writing any.",
        reads="Config and routed conduct files (CLAUDE.md for claude and qwen, AGENTS.md otherwise).",
        writes="Each routed conduct file whose block is missing or stale; nothing when current.",
        lock="None.",
        exits="0 when refreshed or current; 2 on refusal (config error or corrupt markers).",
        examples=["clutch host core"],
    )
    _command(
        host_sub,
        "docs",
        summary="print installed host guide paths",
        does="Print the path and purpose of each host guide shipped in the installed package.",
        reads="Nothing; no config.",
        writes="Nothing.",
        lock="None.",
        exits="0.",
        examples=["clutch host docs"],
    )
    _command(
        host_sub,
        "doctor",
        summary="inspect setup without changing state",
        does="Check setup, managed conduct blocks, parallel provider concurrency, graphics judge independence and panel provider concurrency, printing PASS or FAIL rows and WARN rows for overdue retro and calibration; these run only when invoked.",
        reads="Config, git, the writer lock, journal and routed conduct files at HEAD.",
        writes="Nothing.",
        lock="None; probes the writer lock and fails while another process holds it.",
        exits="0 when every check passes; 2 when any fails.",
        examples=["clutch host doctor"],
    )
    prompt = sub.add_parser(
        "prompt",
        help="render an operator prompt",
        description="Render prompts for operators.",
        epilog="Examples:\nclutch prompt diagnose example\n  Diagnose the example ticket.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    prompt_sub = prompt.add_subparsers(dest="kind", required=True)
    for kind in ask.KINDS:
        example = f"clutch prompt {kind}" + ("" if ask.TAKES[kind] == "none" else " example")
        command = _command(
            prompt_sub,
            kind,
            summary=ask.DESCRIPTIONS[kind],
            does=ask.DESCRIPTIONS[kind],
            reads="Config, prompt templates and relevant ticket or state data.",
            writes="Nothing; prints the prompt.",
            lock="None.",
            exits="0 on success; 2 on refusal.",
            examples=[example],
        )
        command.add_argument("stems", nargs="*")
    host_prompt = _command(
        prompt_sub,
        "host",
        summary="render a host prompt",
        does="Render a named host prompt.",
        reads="Config and host prompt files.",
        writes="Prompt to stdout.",
        lock="None.",
        exits="0 on success; 2 on refusal.",
        examples=["clutch prompt host notes example"],
    )
    host_prompt.add_argument("name")
    host_prompt.add_argument("stems", nargs="*")
    _command(
        prompt_sub,
        "list",
        summary="list available prompts",
        does="List engine and host prompts.",
        reads="Config and host prompt files.",
        writes="Catalog to stdout and problems to stderr.",
        lock="None.",
        exits="0 on success; 2 on invalid host prompts.",
        examples=["clutch prompt list"],
    )
    help_parser = _command(
        sub,
        "help",
        summary="show command help and examples",
        does="Print help for a command path.",
        reads="Command parser definitions.",
        writes="Help to stdout.",
        lock="None.",
        exits="0 on success; 2 for an unknown command.",
        examples=["clutch help roadmap author"],
    )
    help_parser.add_argument("command", nargs="*")
    provider = sub.add_parser(
        "provider",
        help="install and probe provider CLIs",
        description="Install or report provider CLIs and probe declared providers' models.",
        epilog="Examples:\nclutch provider install\n  Report provider CLIs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    provider_sub = provider.add_subparsers(dest="provider_verb", required=True)
    install = _command(
        provider_sub,
        "install",
        summary="install provider CLIs into the host project as pnpm dev dependencies",
        does="Install named provider CLIs as pnpm dev dependencies, then report their package, location and version; with no names, report every adapter.",
        reads="Provider CLI --version output from node_modules/.bin or PATH; no config.",
        writes="With names, package.json, pnpm-lock.yaml, pnpm-workspace.yaml and node_modules/ through pnpm; otherwise nothing.",
        lock="None.",
        exits="0 when installed or reported; 2 on refusal (unknown provider, pnpm missing, pnpm add failed, or CLI printed no version after install).",
        examples=["clutch provider install", "clutch provider install claude codex"],
    )
    install.add_argument("providers", nargs="*")
    probe = _command(
        provider_sub,
        "probe",
        summary="probe declared providers",
        does="Probe each distinct model of named declared providers, or every declared provider, and print each result.",
        reads="Config and declared provider CLIs.",
        writes="Nothing kept; scratch prompts under <state_dir>/evidence/scratch/ are removed after each call.",
        lock="None.",
        exits="0 when every probe answers; 1 on probe or provider setup failure; 2 for an undeclared provider or refusal.",
        examples=["clutch provider probe", "clutch provider probe claude"],
    )
    probe.add_argument("providers", nargs="*")
    config_parser = sub.add_parser(
        "config",
        help="create, check and migrate config.yaml",
        description="Suggest a config.yaml from provider CLIs, compare configured model names with those served, and migrate an older config schema.",
        epilog="Examples:\nclutch config init\n  Suggest a configuration.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    config_sub = config_parser.add_subparsers(dest="config_verb", required=True)
    init = _command(
        config_sub,
        "init",
        summary="print a suggested config.yaml from the provider CLIs found",
        does="Print a suggested config.yaml built from provider CLIs and their model names, validated with the real loader; --write creates it at the checkout root when absent.",
        reads="Provider CLIs in the project or on PATH and their model listings; claude resolves each alias with a small model call. No config is needed.",
        writes="Nothing; with --write, config.yaml.",
        lock="None.",
        exits="0 when printed or written; 2 on refusal (no provider CLI, invalid suggestion, or config.yaml already exists with --write).",
        examples=["clutch config init", "clutch config init --write"],
    )
    init.add_argument("--write", action="store_true")
    _command(
        config_sub,
        "update",
        summary="compare configured model names with provider listings",
        does="List model names served by declared providers and identify configured names as current, replaced, not served or unverified.",
        reads="Config and each declared provider CLI's model listing.",
        writes="Nothing.",
        lock="None.",
        exits="0 when every configured name is current; 1 when a suggestion was printed; 2 on refusal.",
        examples=["clutch config update"],
    )
    _command(
        config_sub,
        "migrate",
        summary="validate and migrate an older config",
        does="Validate the selected config and migrate schema_version: 0 to the current schema in place; a current config is a byte-identical no-op.",
        reads="The selected config (--config before the command, else config.yaml at the checkout root).",
        writes="Original bytes to <config>.bak, then the migrated config; nothing for a current config.",
        lock="None.",
        exits="0 when migrated or already current; 2 on refusal.",
        examples=["clutch config migrate", "clutch --config host.yaml config migrate"],
    )
    box = sub.add_parser(
        "box",
        help="file and settle Suggestion Box messages",
        description="File ideas into the Suggestion Box, settle its messages, and link critical clutch bugs and process gaps upstream.",
        epilog="Examples:\nclutch box triage\n  Settle pending messages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    box_sub = box.add_subparsers(dest="box_verb", required=True)
    suggest = _command(
        box_sub,
        "suggest",
        summary="queue an idea for triage",
        does="File an idea as a suggestion in the Suggestion Box; repeats fold into the existing message and blank summaries are refused.",
        reads="Config and the box.",
        writes="A message under <state_dir>/box/; a journal reopen signal for a tombstoned message.",
        lock="None; files while a writer holds the lock.",
        exits="0 when filed or already in the box; 2 on refusal.",
        examples=['clutch box suggest "<an idea>"'],
    )
    suggest.add_argument("summary")
    triage_parser = _command(
        box_sub,
        "triage",
        summary="settle pending box messages",
        does=(
            "Reap interrupted runs, then make one sequential pass over named pending messages or all pending messages, "
            "settling each as author, tombstone or declined with a model call; refuse unknown ids before the pass. "
            "When an engine holds the lock, submit a request for its next idle point."
        ),
        reads="Config, the box, journal, tickets and git state.",
        writes="Decision records and authored tickets in commits, message resolutions and journal events, or an engine inbox request.",
        lock="Try writer lock; submit to a running engine if held.",
        exits="0 after the pass or submission; 2 on refusal.",
        examples=["clutch box triage", 'clutch box triage "<box id>"'],
    )
    triage_parser.add_argument("ids", nargs="*")
    dismiss = _command(
        box_sub,
        "dismiss",
        summary="dismiss box messages",
        does="Decline named messages as operator decisions without a model call; refuse unknown ids before settling any, and print already-resolved messages' resolutions.",
        reads="Config, the box and journal.",
        writes="tickets/decisions/declined-<id>.md records in commits and message resolutions.",
        lock="Writer lock.",
        exits="0 when dismissed or already resolved; 2 on refusal.",
        examples=["clutch box dismiss example"],
    )
    dismiss.add_argument("ids", nargs="+")
    issue_parser = _command(
        box_sub,
        "issue",
        summary="print a prefilled upstream issue link",
        does="Print a prefilled GitHub new-issue link for a critical clutch bug or a process gap; submit nothing.",
        reads="The --body file and, when it loads, config to scrub configured secrets.",
        writes="Nothing; prints the link.",
        lock="None.",
        exits="0 when printed; 2 on refusal (unknown or missing class, unreadable or empty body, or link over 3,000 bytes).",
        examples=['clutch box issue --class engine-stuck "<title>" --body body.md', 'clutch box issue --class process-gap "<title>" --body body.md'],
    )
    issue_parser.add_argument("--class", dest="issue_class", default=None, help=", ".join(issue.CLASSES))
    issue_parser.add_argument("title")
    issue_parser.add_argument("--body", type=Path, required=True)
    context_parser = sub.add_parser(
        "context",
        help="suggest ticket context",
        description="Suggest ticket context. Subcommands: suggest.",
        epilog="Examples:\nclutch context suggest my-ticket\n  Suggest ticket context.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    context_sub = context_parser.add_subparsers(dest="context_verb", required=True)
    context_suggest = _command(
        context_sub,
        "suggest",
        summary="suggest ticket context",
        does="Suggest files and sections for a ticket.",
        reads="The ticket file and <state_dir>/index.duckdb.",
        writes="Nothing; prints suggestions.",
        lock="None; read-only, works while serve runs.",
        exits="0 suggested or none; 1 none with --require; 2 refused, no_index or index_unreadable.",
        examples=["clutch context suggest my-ticket", "clutch context suggest my-ticket --require"],
    )
    context_suggest.add_argument("stem")
    context_suggest.add_argument("--require", action="store_true", help="Exit 1 when no selectors are suggested.")
    index_parser = sub.add_parser(
        "index",
        help="build the project index",
        description="Build the project index. Subcommands: build.",
        epilog="Examples:\nclutch index build\n  Build the project index.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    index_sub = index_parser.add_subparsers(dest="index_verb", required=True)
    _command(
        index_sub,
        "build",
        summary="build the project index",
        does="Build or refresh the project index.",
        reads="Config, tracked files, git history, evidence store, Suggestion Box and index.embed command output.",
        writes="<state_dir>/index.duckdb.",
        lock="Writer lock.",
        exits="0 built; 1 built with findings; 2 not built or refused.",
        examples=["clutch index build"],
    )
    meta_parser = sub.add_parser(
        "meta",
        help="maintain file metadata",
        description="Maintain metadata on configured files. Subcommands: refresh, check, fill.",
        epilog="Examples:\nclutch meta check\n  Check configured files.\nclutch meta fill tests/\n  Fill metadata.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    meta_sub = meta_parser.add_subparsers(dest="meta_verb", required=True)
    for verb in ("refresh", "check", "fill"):
        command = _command(
            meta_sub,
            verb,
            summary=f"{verb} file metadata",
            does=f"{verb.capitalize()} metadata on configured files.",
            reads="Config, tracked files and HEAD.",
            writes="Metadata blocks." if verb in ("refresh", "fill") else "Nothing; prints findings.",
            lock={"refresh": "Commit lock only.", "fill": "Writer lock.", "check": "None."}[verb],
            exits="0 on success; 1 for findings; 2 on refusal.",
            examples=[f"clutch meta {verb} tests/"],
        )
        command.add_argument("paths", nargs="*")
    roadmap = sub.add_parser(
        "roadmap",
        help="maintain roadmap tickets",
        description="Maintain and inspect roadmap releases and tickets.",
        epilog="Examples:\nclutch roadmap status\n  Show roadmap progress.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    roadmap_sub = roadmap.add_subparsers(dest="roadmap_verb", required=True)
    author = _command(
        roadmap_sub,
        "author",
        summary="author ready roadmap rows",
        does="Author ready roadmap rows and maintain links.",
        reads="Roadmap, tickets, journal and config.",
        writes="Tickets and roadmap links in commits; journal state.",
        lock="Writer lock.",
        exits="0 on success; 2 on refusal.",
        examples=["clutch roadmap author --ahead 2"],
    )
    author.add_argument("--ahead", type=int, default=None, help="open rows to keep authored ahead (default: config roadmap.ahead)")
    _command(
        roadmap_sub,
        "status",
        summary="show read-only roadmap progress",
        does="Show roadmap progress and waiting rows.",
        reads="Roadmap, tickets and journal.",
        writes="Nothing; prints progress.",
        lock="None.",
        exits="0 on success; 2 on refusal.",
        examples=["clutch roadmap status"],
    )
    accept = _command(
        roadmap_sub,
        "accept",
        summary="review a release against its promises",
        does="Review a release against its promises and append gap rows.",
        reads="Roadmap, release plans, tickets and config.",
        writes="Gap rows in a roadmap commit.",
        lock="Commit lock only.",
        exits="0 when promises hold; 1 for gaps; 2 on refusal.",
        examples=["clutch roadmap accept 1.0.0"],
    )
    accept.add_argument("release")
    gate = _command(
        roadmap_sub,
        "gate",
        summary="run a release's ship gate",
        does="Run a release's ship gate in order.",
        reads="Roadmap gate commands and config.",
        writes="Gate result to the journal; commands may write files.",
        lock="None.",
        exits="0 when passing; 1 on failure; 2 on refusal.",
        examples=["clutch roadmap gate 1.0.0"],
    )
    gate.add_argument("release")
    merged = _command(
        roadmap_sub,
        "merged",
        summary="check merged roadmap conditions",
        does="Check roadmap settlement and merge counts, with a parallel overlap filter and conflict-rerun cap check.",
        reads="Roadmap, tickets, journal and git history.",
        writes="Nothing; prints conditions.",
        lock="None.",
        exits="0 when conditions hold; 1 otherwise; 2 on refusal.",
        examples=["clutch roadmap merged example", "clutch roadmap merged --since v0.4.0 --at-least 10 --parallel"],
    )
    merged.add_argument("stems", nargs="*")
    merged.add_argument("--release")
    merged.add_argument("--priority", nargs="+", choices=PRIORITIES)
    merged.add_argument("--since")
    merged.add_argument("--at-least", type=int)
    merged.add_argument("--source")
    merged.add_argument("--unattended", action="store_true")
    merged.add_argument("--parallel", action="store_true")
    release = sub.add_parser(
        "release",
        help="bump, tag and publish releases",
        description="Bump, publish or ship a release. Subcommands: bump, publish, ship.",
        epilog="Examples:\nclutch release publish\n  Build the tagged release.\nclutch release ship\n  Gate and ship the current release.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    release_sub = release.add_subparsers(dest="release_verb", required=True)
    bump = _command(
        release_sub,
        "bump",
        summary="bump, commit, and tag a local release without publishing",
        does="Bump the version with uv, write a changelog section, commit the version files, tag the release and journal a release signal; publish nothing.",
        reads="Config, git status of the version files, uv's next-version preview, existing tags and subjects merged since the previous release tag.",
        writes="pyproject.toml, uv.lock and CHANGELOG.md in one commit, an annotated tag and one journal signal.",
        lock="Writer lock; refuses while another process holds it.",
        exits="0 when tagged; 2 on refusal (dirty version files, existing tag, uv failure or held lock).",
        examples=["clutch release bump --minor", "clutch release bump --patch"],
    )
    part = bump.add_mutually_exclusive_group(required=True)
    part.add_argument("--minor", dest="part", action="store_const", const="minor")
    part.add_argument("--patch", dest="part", action="store_const", const="patch")
    _command(
        release_sub,
        "publish",
        summary="build the tagged release and upload it when release.publish is true",
        does="Build the version tagged at HEAD into <state_dir>/dist and list artifacts; upload only with release.publish: true; never bump.",
        reads="Config, tracked tree git status, uv's version, HEAD and its tag, and the variable named by release.pypi_token.",
        writes="Wheel and sdist under <state_dir>/dist, emptied on each run; an upload when enabled; no commit, tag or journal event.",
        lock="Writer lock; refuses while another process holds it.",
        exits="0 when built (and uploaded when enabled); 2 on refusal (missing token, dirty tracked tree, missing or misplaced tag, uv failure or held lock).",
        examples=["clutch release publish"],
    )
    _command(
        release_sub,
        "ship",
        summary="gate and ship the current release",
        does="Run the current release gate, bump and tag, optionally publish, then run configured packages.",
        reads="Config, roadmap gate, git state and version files.",
        writes="Gate and release journal signals, version files, tag, packages and optional PyPI upload.",
        lock="Writer lock; refuses while held.",
        exits="0 on success; 1 on gate failure; 2 on refusal.",
        examples=["clutch release ship"],
    )
    evidence = sub.add_parser(
        "evidence",
        help="inspect and normalize captured evidence",
        description="Inspect always-on evidence capture. Subcommands: show, schema, renormalize, coverage, captures, prune.",
        epilog="Examples:\nclutch evidence show llm/example/1/implement/0/1\nclutch evidence schema event\nclutch evidence renormalize\nclutch evidence coverage\nclutch evidence captures example\nclutch evidence prune --to-gb 1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    evidence_sub = evidence.add_subparsers(dest="evidence_verb", required=True)
    show = _command(
        evidence_sub,
        "show",
        summary="show a captured call",
        does="Print start.json, end.json and stored normalized event lines (seq, t_ms, kind, native_type).",
        reads="Config and the selected evidence call.",
        writes="Stdout only.",
        lock="None.",
        exits="0 on success; 2 for an unknown key or unreadable store.",
        examples=["clutch evidence show llm/example/1/implement/0/1"],
    )
    show.add_argument("call_key")
    schema = _command(
        evidence_sub,
        "schema",
        summary="print an evidence JSON Schema",
        does="Print the generated JSON Schema for an evidence record.",
        reads="Evidence schema models.",
        writes="Stdout only.",
        lock="None.",
        exits="0 on success; 2 for an unknown record name or invalid config.",
        examples=["clutch evidence schema event"],
    )
    schema.add_argument("record", choices=("start", "end", "event"))
    renormalize = _command(
        evidence_sub,
        "renormalize",
        summary="rebuild normalized evidence views",
        does="Normalize stored raw stdout with current provider normalizers; count calls skipped for missing raw data, unfinished calls or unsupported providers and versions.",
        reads="Config, call envelopes, raw stdout and arrival times.",
        writes="Only normalized/*.json views and blobs under <state_dir>/evidence; preserves other normalizer ids. No journal event.",
        lock="None.",
        exits="0 on success; 2 for an unreadable store.",
        examples=["clutch evidence renormalize --prefix llm/example/"],
    )
    renormalize.add_argument("--prefix", default="", metavar="KEY_PREFIX")
    _command(
        evidence_sub,
        "coverage",
        summary="report normalized event coverage",
        does="Print known-event percentages and common unknown native types by provider and CLI version, and unknown-version skip counts.",
        reads="Config, call envelopes and normalized views.",
        writes="Stdout only.",
        lock="None.",
        exits="0 on success; 2 for an unreadable store.",
        examples=["clutch evidence coverage"],
    )
    captures = _command(
        evidence_sub,
        "captures",
        summary="list or print ticket captures",
        does="List captures for a ticket or print one named capture. Attempts start at attempt 0; spool run sequences appear as a leading run-<n>/ name segment.",
        reads="Config and capture pointers and blobs.",
        writes="Stdout only; no journal event.",
        lock="None.",
        exits="0 on success; 2 for invalid input or unreadable or missing capture.",
        examples=["clutch evidence captures example --attempt 1 --name implement/prompt.md"],
    )
    captures.add_argument("stem")
    captures.add_argument("--attempt", type=int)
    captures.add_argument("--name")
    prune = _command(
        evidence_sub,
        "prune",
        summary="delete oldest eligible evidence blobs",
        does="Prune eligible blobs to the requested size and print sizes before and after.",
        reads="Config, evidence blobs and records.",
        writes="Deletes eligible evidence blobs; records remain.",
        lock="Writer lock; refuses while held.",
        exits="0 on success; 2 for a negative target, held lock or unreadable store.",
        examples=["clutch evidence prune --to-gb 1"],
    )
    prune.add_argument("--to-gb", type=int, required=True, metavar="N")
    training = sub.add_parser(
        "training",
        help="export training data and evaluate review routes",
        description="Export training data and evaluate review routes from local evidence. Subcommands: export, eval.",
        epilog="Examples:\nclutch training export --out training-data\nclutch training eval --route medium/review --holdout training-data/holdout.txt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    training_sub = training.add_subparsers(dest="training_verb", required=True)
    export = _command(
        training_sub,
        "export",
        summary="export training records",
        does="Export labelled training records, including implement trajectories unless --no-trajectory is given and file_purposes when indexed paths match.",
        reads="Config, evidence, first-parent git commits, the optional index and box messages for triage.",
        writes="Requested JSONL files and optional holdout list under --out, replaced whole.",
        lock="None.",
        exits="0 on success; 2 when disabled, refused, or --require-records finds a requested kind empty.",
        examples=["clutch training export --out training-data --kinds ticket triage --since 2026-11-10 --require-records"],
    )
    export.add_argument("--out", type=Path, required=True)

    def export_date(value):
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError(value)
            date.fromisoformat(value)
            return value
        except ValueError:
            raise argparse.ArgumentTypeError("expected a valid YYYY-MM-DD date") from None

    export.add_argument("--kinds", nargs="+", choices=("implement", "preference", "review", "diagnosis", "ticket", "conflict", "triage"), default=["implement", "preference", "review", "diagnosis"])
    export.add_argument("--since", type=export_date, metavar="DATE", help="include calls on or after YYYY-MM-DD")
    export.add_argument("--no-trajectory", action="store_false", dest="trajectory", help="omit implement tool-call trajectories")
    export.add_argument("--holdout", type=int, choices=range(101), default=0, metavar="PCT")
    export.add_argument("--require-records", action="store_true", help="refuse if any requested kind has no records")
    evaluation = _command(
        training_sub,
        "eval",
        summary="score a review route against held-out records",
        does="Replay held-out review prompts and print agreement with recorded negative or neutral labels.",
        reads="Config, holdout stems, evidence and first-parent git commits; calls the selected model route.",
        writes="Report to stdout only; no journal, evidence records or engine log.",
        lock="None.",
        exits="0 on success; 2 when disabled, the route is invalid, the holdout is unreadable, provider setup fails or no held-out review record was scored.",
        examples=["clutch training eval --route medium/review --holdout training-data/holdout.txt"],
    )
    evaluation.add_argument("--route", choices=[f"{tier}/review" for tier in TIERS], required=True)
    evaluation.add_argument("--holdout", type=Path, required=True)
    coverage = sub.add_parser(
        "coverage",
        help="build and check coverage reports",
        description="Build a coverage map or check coverage thresholds.",
        epilog="Examples:\nclutch coverage map\n  Build the coverage map.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    coverage_sub = coverage.add_subparsers(dest="coverage_verb", required=True)
    _command(
        coverage_sub,
        "map",
        summary="build the coverage map",
        does="Run review.coverage_map.argv and map covered source files to the tests that ran them for requisition review.",
        reads="Config (review.coverage_map), the command's JSON report and the main commit.",
        writes="<state_dir>/coverage-map.json, replaced whole; deletes the configured report before and after the run.",
        lock="None.",
        exits="0 on success; 2 on refusal (invalid config, missing setting, failed command or missing or invalid report).",
        examples=["clutch coverage map"],
    )
    covgate = _command(
        coverage_sub,
        "gate",
        summary="check a coverage JSON report against thresholds",
        does="Run the unit-test command after -- in the invocation directory, then check its fresh coverage report and print each threshold failure.",
        reads="Gate file (--gate, default test-gate.toml) and report (--report, default coverage.json), relative to the invocation directory; no config.",
        writes="Nothing itself; deletes the report before the run.",
        lock="None.",
        exits="0 on coverage pass; 1 on threshold failures; 2 on refusal; otherwise the command's own nonzero code.",
        examples=["clutch coverage gate -- python -m pytest tests/unit --cov=clutch --cov-report=json:coverage.json"],
    )
    covgate.add_argument("--gate", type=Path, default=Path("test-gate.toml"))
    covgate.add_argument("--report", type=Path, default=Path("coverage.json"))
    covgate.add_argument("command", nargs=argparse.REMAINDER)
    ticket = sub.add_parser(
        "ticket",
        help="author and maintain tickets",
        description="Author, validate, review, order, confirm and reject tickets.",
        epilog="Examples:\nclutch ticket lint example\n  Validate a ticket.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ticket_sub = ticket.add_subparsers(dest="ticket_verb", required=True)
    new = _command(
        ticket_sub,
        "new",
        summary="create and lint a ticket skeleton",
        does="Create and lint a ticket skeleton; bugs require evidence and graphics can include reference and input files.",
        reads="Evidence, reference and input files; no config is needed.",
        writes="Ticket file and copied evidence or graphics files; no journal or git state.",
        lock="None.",
        exits="0 when authored; 2 on refusal.",
        examples=["clutch ticket new add-widget", "clutch ticket new fix-crash --kind bug --evidence crash.txt", "clutch ticket new hero --kind graphics --reference mock.png --input product.png"],
    )
    new.add_argument("stem")
    new.add_argument("--kind", choices=KINDS, default="feature")
    new.add_argument("--evidence", nargs="+", metavar="PATH")
    new.add_argument("--reference", nargs="+", metavar="PATH")
    new.add_argument("--input", nargs="+", metavar="PATH")
    lint = _command(
        ticket_sub,
        "lint",
        summary="validate tickets without writing",
        does="Validate tickets and graphics judge independence without running them.",
        reads="Tickets, journal (the main checkout's in a linked worktree), git status and config.",
        writes="Nothing.",
        lock="None.",
        exits="0 when valid; 1 for findings; 2 for a missing named ticket or unreadable tickets directory.",
        examples=["clutch ticket lint add-widget"],
    )
    lint.add_argument("stems", nargs="*")
    review = _command(
        ticket_sub,
        "review",
        summary="review a committed ticket",
        does="Commit only named ticket edits through intake and review each committed ticket with a model.",
        reads="Tickets, journal, git state and config.",
        writes="Named ticket commits and journal verdicts; provisional reviews with unmerged dependencies are printed only.",
        lock="Commit lock only.",
        exits="0 on approve; 1 on snag or rma; 2 on refusal.",
        examples=["clutch ticket review add-widget"],
    )
    review.add_argument("stems", nargs="+")
    ordering = _command(
        ticket_sub,
        "order",
        summary="edit ticket priority or ordering",
        does="Edit priority and runs-before ordering for intake to commit.",
        reads="Ticket, journal and lock holder.",
        writes="Ticket in the working tree.",
        lock="None.",
        exits="0 when edited; 2 on refusal.",
        examples=["clutch ticket order add-widget --priority P0", "clutch ticket order add-widget --runs-before"],
    )
    ordering.add_argument("stem")
    ordering.add_argument("--priority", choices=PRIORITIES)
    ordering.add_argument("--runs-before", nargs="*", metavar="STEM")
    for verb in ("confirm", "reject"):
        does = (
            "Keep each draft or Reject-queue stem, resetting its caps; refuse running stems, stems outside those states and unchanged repeat keeps without --extension."
            if verb == "confirm"
            else "Reject each stem, stamp and commit it, journal the kill and file failure reports for confirmed dependents; refuse running and settled stems."
        )
        verdict = _command(
            ticket_sub,
            verb,
            summary=f"{verb} a draft or Reject-queue ticket",
            does=does + " A person answers y at a terminal unless --yes or --extension is given.",
            reads="Tickets, journal, git state and config.",
            writes=(
                "Named ticket pending edits through intake, then a clutch(<stem>): confirmed commit and draft_confirmed signal or reject_verdict keep signal; "
                if verb == "confirm"
                else "Named ticket pending edits through intake, then a clutch(<stem>): rejected commit, reject_verdict kill with optional --reason and rejected events and dependent box messages; "
            )
            + "with drain or serve running, submit a verdict request instead. Acceptance is not completion; serve applies ticket verdicts during active Check or model work.",
            lock="Writer lock; publish to a running drain or serve holding it, refuse any other holder.",
            exits="0 when applied or submitted; 1 when the prompt is not answered y; 2 on refusal.",
            examples=[f"clutch ticket {verb} add-widget", f"clutch ticket {verb} --yes add-widget"] + (['clutch ticket reject --yes --reason "scope too wide" add-widget'] if verb == "reject" else []),
        )
        verdict.add_argument("stems", nargs="+")
        verdict.add_argument("--yes", action="store_true")
        verdict.add_argument("--extension", action="store_true")
        if verb == "reject":
            verdict.add_argument("--reason")
    engine = sub.add_parser(
        "engine",
        help="run and control the engine",
        description="Run tickets, control a running engine, and run retros and estimate calibrations only when invoked; view status and host doctor report overdue maintenance.",
        epilog="Examples:\nclutch engine drain\n  Run eligible tickets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    engine_sub = engine.add_subparsers(dest="engine_verb", required=True)
    dr = _command(
        engine_sub,
        "drain",
        summary="run eligible tickets to quiescence",
        does="Run every eligible ticket to quiescence.",
        reads="Config, tickets and journal.",
        writes="Ticket commits, journal events and engine state; --detach appends to <state_dir>/drain.out in its own session.",
        lock="Writer lock; the child takes it with --detach.",
        exits="0 at quiescence; 1 when halted or killed; 2 on refusal.",
        examples=["clutch engine drain", "clutch engine drain --detach"],
    )
    dr.add_argument("--detach", action="store_true", help="run in its own session and append to <state_dir>/drain.out")
    dr.add_argument("--parked", action="append", default=[], metavar="STEM", help="a stem the handing-off parent drain parked (set by the self-upgrade re-exec)")
    dr.add_argument("--deadline", type=datetime.fromisoformat, default=None, help="deadline set by the self-upgrade re-exec")
    dr.add_argument("--stop-lifecycle", help=argparse.SUPPRESS)
    _command(
        engine_sub,
        "serve",
        summary="run the continuous daemon",
        does="Run the continuous daemon until engine kill, engine stop or a signal.",
        reads="Config, tickets and journal.",
        writes="Ticket commits, journal events and engine state.",
        lock="Writer lock.",
        exits="0 after kill, stop or a signal; 1 when a component fails; 2 on refusal.",
        examples=["clutch engine serve"],
    )
    run = _command(
        engine_sub,
        "run",
        summary="drive one ticket through the pipeline",
        does="Drive one ticket through intake and every stage.",
        reads="Config, ticket and journal.",
        writes="Ticket commits, journal events and engine state.",
        lock="Writer lock.",
        exits="0 when merged; 1 for a non-ok terminal; 2 on refusal.",
        examples=["clutch engine run example"],
    )
    run.add_argument("stem")
    _command(
        engine_sub,
        "stop",
        summary="finish active work and exit",
        does="Request a running drain or serve to finish its ticket, admit nothing new and exit; refuse when nothing runs or a non-engine holder has the lock.",
        reads="Engine lock and state.",
        writes="A stop request.",
        lock="Writer lock only to probe.",
        exits="0 when submitted; 2 on refusal.",
        examples=["clutch engine stop"],
    )
    _command(
        engine_sub,
        "pause",
        summary="pause ticket admission",
        does="Ask a running drain or serve to admit no new ticket until engine resume; print nothing running to pause when idle; refuse a non-engine lock holder.",
        reads="Engine lock and state.",
        writes="A pause request to <state_dir>/control/inbox/ when an engine runs.",
        lock="Writer lock only to probe.",
        exits="0 when submitted or nothing runs; 2 on refusal.",
        examples=["clutch engine pause"],
    )
    _command(
        engine_sub,
        "resume",
        summary="release the current hold",
        does=(
            "Ask a running drain or serve to release its current advertised hold (pause, storm trip or red streak); "
            "print nothing running to resume when idle; refuse if no hold is advertised or a non-engine holder has the lock."
        ),
        reads="Engine lock and state.",
        writes="A resume request to <state_dir>/control/inbox/ when an engine runs.",
        lock="Writer lock only to probe.",
        exits="0 when submitted or nothing runs; 2 on refusal.",
        examples=["clutch engine resume"],
    )
    _command(
        engine_sub,
        "kill",
        summary="abort active work and stop",
        does="Ask a running drain or serve to stop at the next safe point, aborting its running ticket; refuse when nothing runs or a non-engine holder has the lock.",
        reads="Engine lock and state.",
        writes="A kill request to <state_dir>/control/inbox/.",
        lock="Writer lock only to probe.",
        exits="0 when submitted; 2 on refusal.",
        examples=["clutch engine kill"],
    )
    _command(
        engine_sub,
        "retro",
        summary="run or queue a retro report",
        does="Run a retro report only when invoked, now or queued on a running drain or serve; view status and host doctor report overdue retros. Refuse a non-engine lock holder.",
        reads="Config, journal, tickets and engine state.",
        writes="A committed tickets/retro/NNNNNN.md report or a retro request to <state_dir>/control/inbox/.",
        lock="Writer lock, or queue on the running engine.",
        exits="0 when committed, nothing merged since the last report, or queued; 1 when no report is committed; 2 on refusal.",
        examples=["clutch engine retro"],
    )
    _command(
        engine_sub,
        "calibrate",
        summary="journal actual Implement minutes against ticket estimates",
        does=(
            "Compute, per provider and model, the run count, median estimate, and median and 90th-percentile actual minutes "
            "of the last calibration.every completed Implement calls; journal them as an estimate_calibration signal and print the table. Run only when invoked; view status and host doctor report overdue calibration."
        ),
        reads="Config, journal, and tickets of stems in the window.",
        writes="One estimate_calibration journal signal.",
        lock="None; journal append takes journal.lock.",
        exits="0 when recorded; 2 on refusal.",
        examples=["clutch engine calibrate"],
    )
    # Replace argparse's flat choice listing with one ordered command listing.
    sub.help = argparse.SUPPRESS
    lines = ["Commands:"]
    for action in sub._choices_actions:
        lines.append(f"  {action.dest}  {action.help}")
        child = _subparsers(sub.choices[action.dest])
        if child:
            lines.extend(f"  {action.dest} {item.dest}  {item.help}" for item in child._choices_actions)
    ap.epilog = "\n".join(lines) + "\n\nRun clutch help <command> for command help."
    ap.formatter_class = argparse.RawDescriptionHelpFormatter
    return ap


def _run_context_suggest(config, root, stem, *, fs, connect=duckdb.connect, require=False):
    if not tickets.STEM.fullmatch(stem) or stem in tickets.RESERVED_STEMS:
        return _fail("context suggest", "refused: invalid stem -- choose a valid ticket stem")
    path = root / ticket_path(stem)
    try:
        body = fs.read_bytes(path).decode("utf-8")
    except OSError, UnicodeDecodeError:
        return _fail("context suggest", "refused: ticket is missing or unreadable UTF-8 -- create a readable ticket")
    sections, _ = tickets._sections(body, str(path))
    for name in ("Goal / Why", "Scope fence"):
        if not sections.get(name, "").strip():
            return _fail("context suggest", f"refused: missing or blank {name} -- fill in ## {name}")
    fence, _ = tickets._bullets(sections["Scope fence"], "Scope fence", str(path))
    entries, _ = tickets._bullets(sections.get("Context", ""), "Context", str(path))
    database = config.state_dir / "index.duckdb"
    try:
        fs.size(database)
    except FileNotFoundError:
        return _fail("context suggest", "no_index -- run clutch index build")
    except OSError:
        return _fail("context suggest", "index_unreadable -- retry after the running refresh finishes, or run clutch index build if the index lacks a table")
    try:
        conn = connect(str(database), read_only=True)
        try:
            files, chunks = context.suggest(conn, stem, fence, entries, sections["Goal / Why"])
        finally:
            conn.close()
    except duckdb.Error:
        return _fail("context suggest", "index_unreadable -- retry after the running refresh finishes, or run clutch index build if the index lacks a table")
    lines = files + chunks
    print("context suggest: suggested" if lines else "context suggest: none")
    for selector, reason in lines:
        print(f"- {selector}  # {reason}")
    return 1 if require and not lines else 0


async def _run_index(config, root, *, fs, git, exec_, env, store, creator, build=index.build):
    try:
        findings = await build(config, root, fs=fs, git=git, exec_=exec_, env=child_env(env, config, serving=None), store=store, creator=creator)
    except Exception as exc:
        return _fail("index build", f"build raised {type(exc).__name__}: {exc} -- resolve the error and retry clutch index build")
    exits = [INDEX_FINDING_EXITS.get(f.partition(": ")[0], 2) if ": " in f else 2 for f in findings]
    if 2 in exits:
        finding = next(f for f, code in zip(findings, exits) if code == 2)
        return _fail("index build", f"{finding} -- resolve the finding and retry clutch index build")
    if findings:
        print("index build: built_with_findings")
        for finding in findings:
            print(finding)
        return 1
    print("index build: built")
    return 0


async def _run_meta(verb, config, root, fs, tracked, sha, paths=(), ask=None):
    from clutch import meta

    missing = [path for path in paths if not any(meta._files(config, tracked, (path,)))]
    if missing:
        for path in missing:
            _fail(f"meta {verb}", f"{path}: selects no tracked file -- for a new file, run git add -N {path} then rerun; otherwise name a .md or .py path under a configured meta.paths root")
        return 2

    if verb == "refresh":
        changed, malformed = meta.refresh(config, root, fs, tracked, sha, paths)
        for path in changed:
            print(path)
        for path in malformed:
            _fail("meta refresh", f"{path}: malformed -- fix or remove the block so it has schema plus the six keys with a valid kind, then rerun clutch meta refresh")
        return 2 if malformed else 0
    if verb == "fill":
        from clutch import metafill
        from clutch.runner import SPECS_DIR
        from clutch.specs import load_spec

        spec = load_spec((SPECS_DIR / "meta.md").read_text())
        changed, rejected = await metafill.fill(config, root, fs, tracked, sha, spec, ask, paths)
        for path in changed:
            print(path)
        for path, reason in rejected:
            _fail("meta fill", f"{path}: {reason}")
        return 2 if any(reason in ("malformed", "infra_error", "timeout", "render_over_bound") for _, reason in rejected) else 1 if rejected else 0
    findings = meta.check(config, root, fs, tracked, sha, paths)
    for path, reason in findings:
        print(f"{path}: {reason}")
    return 1 if findings else 0


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
    parser = _parser()
    if invocation and invocation[0] in ("--help", "-h"):
        invocation = ["help", *invocation[1:]]
    args = parser.parse_args(invocation)
    if args.verb == "help":
        target = parser
        for word in args.command:
            children = _subparsers(target)
            if children is None or word not in children.choices:
                return _fail("help", f"unknown command {' '.join(args.command)} -- run clutch help to list commands")
            target = children.choices[word]
        target.print_help()
        return 0
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
            ("training", "training data export and evaluation"),
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
                raise runner.Refusal("no provider CLI found", f"run: clutch provider install {'|'.join(sorted(ADAPTERS))}") from None

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
                        rc, _, err = await exec_.run(["pnpm", "add", "-D", f"--allow-build={package}", f"{package}@latest"], cwd=repo, env=tool_env(env, repo), timeout=INSTALL_TIMEOUT_S)
                    except ExecutableNotFound:
                        raise runner.Refusal("pnpm is not on PATH", "install pnpm (https://pnpm.io/installation), then rerun clutch provider install") from None
                    if rc:
                        lines = [line for line in err.splitlines() if line.strip()]
                        raise runner.Refusal(f"pnpm add {package}@latest failed (rc {rc}): {lines[-1] if lines else ''}", "fix the pnpm error, then rerun clutch provider install")
                status = await cli_status(name, exec_=exec_, env=env, cwd=repo)
                if args.providers and status.version is None:
                    raise runner.Refusal(f"{name} CLI printed no version after install", f"rerun clutch provider install {name}; if this repeats, check that pnpm allowed the package's build script")
                print(
                    f"{status.name}: {status.where}{' ' + status.version if status.version else ''}, package {status.package}"
                    + (f" -- run: clutch provider install {name}" if status.where == "absent" else "")
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
            return _fail(args.verb, "name the unit-test command after --")
        command = args.command[1:]
        # ProcessExec starts a new session, orphaning the test run when Check kills
        # coverage gate's group on timeout; inheriting the group carries the kill to it.
        try:
            return run_gate(command, gate_path=repo / args.gate, report_path=repo / args.report, run=lambda argv: subprocess.run(argv, cwd=repo, env=env).returncode)
        except FileNotFoundError:
            return _fail(args.verb, f"{command[0]} not found -- install it or correct the command after --")

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
                    raise runner.Refusal(str(exc), f"run: clutch provider install {name}") from None
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
                    req = LLMRequest(surface="preflight", rendered=PROBE_PROMPT, tier=tier, effort="low", subject=model, worktree=None)
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
        if args.view_verb == "snapshot":
            print(json.dumps(observe.snapshot(context, merged_limit=None if args.all_merged else config.snapshot_merged_limit)))
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

    def handle_events():
        from clutch import events

        if not args.once and (args.cursor is not None or args.timeout is not None):
            raise runner.Refusal("--cursor and --timeout require --once", "use clutch view events --once")
        try:
            if args.once:
                try:
                    cursor, lines, timed_out = events.wait_once(config.state_dir, cursor=args.cursor, timeout=300.0 if args.timeout is None else args.timeout, sleep=time.sleep, clock=time.monotonic)
                except ValueError as exc:
                    raise runner.Refusal(str(exc), "provide a valid cursor and nonnegative finite timeout") from exc
                print(json.dumps({"cursor": cursor, "events": lines, "timed_out": timed_out}))
            else:
                events.stream(config.state_dir, sleep=time.sleep, write=lambda line: print(line, flush=True))
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
            return _fail(args.verb, str(exc))
        result = asyncio.run(_stats(checkout, events, now, args.window))
        print(json.dumps(stats_tree(result) if args.tree else result) if args.tree or args.json else render_stats(result), end="\n" if args.tree or args.json else "")
        return 0

    def handle_calibrate():
        from clutch.calibration import calibrate, render

        print(render(calibrate(checkout.journal, checkout.fs, repo, config.calibration.every)), end="")
        return 0

    def handle_status():
        from clutch.evidence.store import EvidenceStore, size_warning

        projection = asyncio.run(_status(checkout))
        print(render(projection, short=True) if args.short else render(projection), end="")
        fs = checkout.fs
        store = EvidenceStore(config.state_dir, fs, fs.read_bytes, fs.size, lambda text: text)
        if message := size_warning(store, config.evidence.warn_gb):
            print(f"evidence: {message}")
        return 0

    # Authoring
    def handle_new():
        return _new(repo, args.stem, args.kind, args.evidence or (), args.reference or (), args.input or ())

    def handle_prompt():
        if args.kind == "list":
            entries, problems = ask.catalog(config, repo)
            for entry in entries:
                print(f"{' '.join(entry['argv'])}\t{entry['takes']}\t{entry['description']}")
            for path, message in problems:
                print(f"{path}: {message}", file=sys.stderr)
            return 2 if problems else 0
        if args.kind == "host":
            if config.prompts_dir is None:
                raise runner.Refusal("prompts_dir is unset", "set prompts_dir in config.yaml")
            entries, problems = ask.catalog(config, repo)
            path = config.prompts_dir / f"{args.name}.md"
            problem = next((message for p, message in problems if p == path), None)
            if problem:
                raise runner.Refusal(f"{path}: {problem}", "repair the host prompt file")
            entry = next((e for e in entries if e["source"] == "host" and e["name"] == args.name), None)
            if entry is None:
                raise runner.Refusal(f"unknown host prompt {args.name!r}", "run clutch prompt list and choose a valid host prompt")
            if len(args.stems) != (1 if entry["takes"] == "stem" else 0):
                raise runner.Refusal(f"host prompt {args.name} takes {entry['takes']}", "supply exactly one ticket stem" if entry["takes"] == "stem" else "omit the stem")
            stem = args.stems[0] if args.stems else ""
            if stem:
                if findings := stem_findings(stem):
                    raise runner.Refusal(findings[0].message, findings[0].paved_road)
                if not (repo / ticket_path(stem)).is_file():
                    raise runner.Refusal(f"{ticket_path(stem)} does not exist", f"author it with clutch ticket new {stem}")
            try:
                result = ask.render_host(args.name, stem, config, repo)
            except ValueError as exc:
                raise runner.Refusal(str(exc), "repair the host prompt file") from None
            print(result, end="")
            return 0
        if ask.TAKES[args.kind] == "none" and args.kind != "drafts":
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
                raise runner.Refusal("no draft tickets await confirm or reject", "run clutch box triage, or author a ticket with clutch ticket new")
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
            raise runner.Refusal(f"{ticket_path(args.stem)} does not exist", f"author it with clutch ticket new {args.stem}")
        from clutch import observe

        last = observe.last_bodies(observe.as_events(observe.journal(config.state_dir)))
        kind = "running" if args.kind == "diagnose" and args.stem in observe.running_stems(config.state_dir, last) else args.kind
        print(ask.render(kind, args.stem, config, repo), end="")
        return 0

    def handle_suggest():
        if not args.summary.strip():
            raise runner.Refusal("blank summary", "pass the idea as one quoted argument")
        from clutch.box import Box, RereportJournal

        box = Box(config.state_dir / BOX_DIR, checkout.fs, rereport=RereportJournal(checkout.journal))
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
        return asyncio.run(_control(checkout, args.engine_verb))

    def handle_verdict():
        for stem in args.stems:
            if result := asyncio.run(_verdict(checkout, stem, args.ticket_verb, read_input, args.yes, args.extension, reason=getattr(args, "reason", None))):
                return result
        return 0

    # Lock holders
    def handle_index():
        from clutch.evidence.store import EvidenceStore

        async def run():
            async with _locked(config.state_dir, "index build", instance_id=await checkout.git.describe(repo), clock=clock):
                redactor = Redactor.from_config(config, env)
                store = EvidenceStore(config.state_dir, checkout.fs, checkout.fs.read_bytes, checkout.fs.size, redactor.scrub)
                return await _run_index(config, repo, fs=checkout.fs, git=checkout.git, exec_=exec_, env=env, store=store, creator=index.default_creator)

        return asyncio.run(run())

    def handle_meta():
        async def run():
            async def execute():
                files = await checkout.git.ls_files(repo)
                sha = await checkout.git.rev_parse(repo, "HEAD")
                if args.meta_verb == "fill":
                    from clutch import metafill
                    from clutch.driver import Driver
                    from clutch.runner import SPECS_DIR
                    from clutch.specs import load_spec

                    session = build_control(checkout).providers
                    try:
                        llm = await _preflighted_llm(checkout, session)
                        driver = Driver.from_config(config, journal=checkout.journal, llm=llm, env=env, clock=clock, sleep=checkout.sleep, fs=checkout.fs)
                        spec = load_spec((SPECS_DIR / "meta.md").read_text())
                        ask = metafill.make_ask(driver, spec, repo, len(checkout.journal.read()))
                        return await _run_meta(args.meta_verb, config, repo, checkout.fs, files, sha, args.paths, ask)
                    finally:
                        await session.close()
                return await _run_meta(args.meta_verb, config, repo, checkout.fs, files, sha, args.paths)

            if args.meta_verb == "refresh":
                async with CommitLock(config.state_dir, clock=clock, sleep=asyncio.sleep):
                    return await execute()
            if args.meta_verb == "fill":
                async with _locked(config.state_dir, f"meta {args.meta_verb}", instance_id=await checkout.git.describe(repo), clock=clock):
                    return await execute()
            return await execute()

        return asyncio.run(run())

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
                roadmap.merged(
                    checkout,
                    args.stems,
                    release=args.release,
                    priorities=args.priority or (),
                    since=args.since,
                    at_least=args.at_least,
                    source=args.source,
                    unattended=args.unattended,
                    parallel=args.parallel,
                )
            )
            print("\n".join(lines))
            return 0 if ok else 1
        ahead = config.roadmap.ahead if args.ahead is None else args.ahead
        if ahead < 1:
            raise runner.Refusal("--ahead must be at least 1", "choose a positive window")

        async def roadmap_pass():
            async with _locked(config.state_dir, "roadmap", instance_id=await checkout.git.describe(repo), clock=clock):
                await runner.reap(checkout)
                session = build_control(checkout).providers
                try:

                    async def author_messages(ids):
                        llm = await _preflighted_llm(checkout, session)
                        await triage.triage_pass(checkout, llm, frozenset(ids))

                    return await roadmap.author_ahead(checkout, ahead, author_messages)
                finally:
                    await session.close()

        print("\n".join(asyncio.run(roadmap_pass())))
        return 0

    def handle_release():
        from clutch import release

        async def release_version():
            async with _locked(config.state_dir, "release", instance_id=await checkout.git.describe(repo), clock=clock):
                version, sha = await release.release(repo, checkout.git, checkout.exec_, checkout.fs, child_env(env, config), args.part, checkout.clock().date().isoformat())
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

    def handle_ship():
        from clutch import release, roadmap

        async def ship_release():
            async with _locked(config.state_dir, "release ship", instance_id=await checkout.git.describe(repo), clock=clock):
                async with checkout.git.main_write():
                    current = roadmap.current_release(repo)
                    if current is None:
                        raise runner.Refusal("no current release", "set a valid project version in pyproject.toml")
                    passed, lines = await roadmap.run_gate(checkout, current)
                    if not passed:
                        return False, lines
                    if config.release.publish:
                        await release.publishable(repo, checkout.git, env, config)
                    version, sha = await release.release(repo, checkout.git, checkout.exec_, checkout.fs, child_env(env, config), "minor", checkout.clock().date().isoformat())
                    release.journal_release(checkout.journal, version, sha)
                    lines.append(f"release: tagged v{version} at {sha}")
                    if config.release.publish:
                        version, _, _ = await release.publish(repo, checkout.git, checkout.exec_, checkout.fs, env, config)
                        lines.append(f"publish: uploaded {version} to PyPI")
                    lines.extend(await release.run_packages(repo, checkout.exec_, checkout.fs, env, config))
                    return True, lines

        passed, lines = asyncio.run(ship_release())
        print("\n".join(lines))
        return 0 if passed else 1

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

        try:
            lines = asyncio.run(one_pass())
        except LockHeld as exc:
            request = asyncio.run(_submit_engine(checkout, exc, "triage", ids=args.ids))
            print(f"triage submitted: {request.request_id}")
            return 0
        print("\n".join(line for _, line in lines) if lines else "no pending suggestions")
        return 0

    def handle_serve():
        return asyncio.run(serve.serve(checkout, config_path=args.config, signals=_engine_signals, argv=invocation, reexec=reexec or SubprocessExec()))

    def handle_retro():
        return asyncio.run(_retro(checkout, pipeline, config_path=args.config))

    def handle_detach():
        output = config.state_dir / "drain.out"
        pid = spawn([sys.executable, "-m", "clutch", *(["--config", str(args.config)] if args.config else []), "engine", "drain"], cwd=repo, env=env, output=output)
        print(f"drain: pid {pid}, output {output}")
        return 0

    def handle_pipeline():
        nonlocal checkout
        checkout = replace(checkout, control=build_control(checkout))
        checkout.control.load_config = _config_reloader(args.config, repo)
        dispatch = pipeline(checkout)
        if args.verb == "engine" and args.engine_verb == "drain":
            from clutch.retro import Retro

            class DrainDispatch:
                _retro = Retro(checkout, dispatch)

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
                    argv=(["--config", str(args.config)] if args.config else []) + ["engine", "drain"],
                )
            )
            if report.handoff is None:
                print(report.render(), end="")
            return report.exit_code
        return asyncio.run(runner.run_ticket(args.stem, checkout, dispatch))

    def handle_evidence():
        from compression.zstd import ZstdError

        from clutch.evidence import views
        from clutch.evidence.schema import json_schema
        from clutch.evidence.store import SKIP, CaptureNotFound, CaptureUnreadable, EvidenceStore

        if args.evidence_verb == "schema":
            print(json.dumps(json_schema(args.record), indent=2))
            return 0
        redactor = Redactor.from_config(config, env)
        store = EvidenceStore(config.state_dir, checkout.fs, checkout.fs.read_bytes, checkout.fs.size, redactor.scrub)
        if args.evidence_verb == "prune":
            if args.to_gb < 0:
                raise runner.Refusal("negative evidence target", "supply a nonnegative --to-gb N")

            async def prune_evidence():
                async with _locked(config.state_dir, "evidence prune", instance_id=await checkout.git.describe(repo), clock=clock):
                    before = store.blob_bytes()
                    store.prune(args.to_gb * 10**9)
                    print(f"evidence blobs: {before} bytes before, {store.blob_bytes()} bytes after")

            asyncio.run(prune_evidence())
            return 0
        if args.evidence_verb == "captures":
            road = f"list what exists with clutch evidence captures {args.stem}"
            if args.name is not None and args.attempt is None:
                raise runner.Refusal("capture name requires an attempt", road)
            try:
                if args.name is not None:
                    print(store.get_capture(args.stem, args.attempt, args.name).decode("utf-8", errors="replace"), end="")
                else:
                    pairs = store.captures(args.stem, args.attempt)
                    print("\n".join(f"{attempt} {name}" for attempt, name in pairs) if pairs else f"no captures for {args.stem}")
                return 0
            except ValueError as exc:
                raise runner.Refusal(f"invalid capture input: {exc}", road) from None
            except CaptureNotFound:
                raise runner.Refusal("no capture for the requested attempt and name", road) from None
            except CaptureUnreadable, OSError:
                raise runner.Refusal("unreadable capture", road) from None
        try:
            if args.evidence_verb == "show":
                start = store.read_record(args.call_key, "start")
                try:
                    end = store.read_record(args.call_key, "end")
                except FileNotFoundError:
                    end = None
                normalized, _ = store.read_normalized(args.call_key)
                print("\n".join(views.show_lines(start, end, normalized)))
                return 0
            skipped = 0
            normalized = 0
            records = []
            for key in store.call_keys(args.prefix if args.evidence_verb == "renormalize" else ""):
                start = store.read_record(key, "start")
                if args.evidence_verb == "coverage":
                    stored, unknown = store.read_normalized(key)
                    skipped += unknown
                    records.append((start, stored))
                    continue
                if start is SKIP or views.normalizer(start.provider.name) is None:
                    skipped += 1
                    continue
                try:
                    end = store.read_record(key, "end")
                    if end is SKIP:
                        skipped += 1
                        continue
                    times = json.loads(store.get_blob(end.raw.stdout_times))
                    stdout = store.get_blob(end.raw.stdout)
                except FileNotFoundError:
                    skipped += 1
                    continue
                view = views.build_view(start, stdout, times, store.put_blob)
                store.write_normalized(key, view["normalizer"], view)
                normalized += 1
            if args.evidence_verb == "renormalize":
                print(f"normalized: {normalized}, skipped: {skipped}")
            else:
                rows, skipped = views.coverage(records, skipped)
                for row in rows:
                    unknown = ", ".join(f"{name}: {count}" for name, count in row["unknown"]) or "none"
                    print(f"{row['provider']} {row['cli_version']}: {row['known_pct']:.1f}% known; unknown: {unknown}")
                print(f"skipped (unknown major version): {skipped}")
            return 0
        except (OSError, ValueError, KeyError, TypeError, IndexError, ZstdError) as exc:
            raise runner.Refusal(f"cannot read or normalize evidence: {exc}", "check the call key and evidence store permissions and records, then retry clutch evidence") from None

    def handle_training():
        from clutch import training
        from clutch.evidence.store import EvidenceStore

        try:
            config.training_data.require_enabled()
        except ValueError as e:
            raise runner.Refusal(f"training {args.training_verb} is off", str(e)) from None
        redactor = Redactor.from_config(config, env)
        store = EvidenceStore(config.state_dir, checkout.fs, checkout.fs.read_bytes, checkout.fs.size, redactor.scrub)
        if args.training_verb == "eval":
            try:
                only = set(checkout.fs.read_bytes(args.holdout).decode().splitlines())
            except (OSError, UnicodeError) as exc:
                raise runner.Refusal(f"cannot read holdout {args.holdout}: {exc}", "pass a readable UTF-8 holdout file from training export") from None

            async def evaluation():
                files, _ = await training.render(store, checkout.git, repo, redactor, config.training_data, checkout.fs.read_bytes, kinds=("review",), only=only)
                session = build_control(checkout).providers
                try:
                    # Eval must not reconstruct or fire journal-backed timers.
                    llm = ProviderLLM(config, exec_=checkout.exec_, fs=checkout.fs, env=env, cwd=repo, timeout=runner.call_timeout(config), session=session)
                    problems = await llm.preflight()
                    if problems:
                        raise ProviderSetupError("; ".join(problems))
                    return await training.evaluate((json.loads(line) for line in files["review.jsonl"].splitlines()), llm, args.route.split("/")[0])
                finally:
                    await session.close()

            counts = asyncio.run(evaluation())
            print(training.report_eval(counts))
            if counts["agree"] + counts["disagree"] == 0:
                raise runner.Refusal("no held-out review record was scored", "run training export with --kinds review and --holdout PCT, then pass its holdout.txt")
            return 0
        index = training.index_files(config.state_dir / "index.duckdb", checkout.fs.size)
        from clutch.box import Box

        box_messages = Box(config.state_dir / BOX_DIR, checkout.fs).messages() if "triage" in args.kinds else ()
        files, counts = asyncio.run(
            training.render(
                store, checkout.git, repo, redactor, config.training_data, checkout.fs.read_bytes, args.kinds, args.holdout, args.trajectory, args.since, index=index, box_messages=box_messages
            )
        )
        for name, data in files.items():
            checkout.fs.write(args.out / name, data)
        for line in training.report(counts):
            print(line)
        if args.require_records:
            missing = [kind for kind in args.kinds if counts[kind] == 0]
            if missing:
                raise runner.Refusal(f"no records for requested kinds: {', '.join(missing)}", "run more tickets with training_data.enabled, or drop the kind from --kinds")
        return 0

    def handle_context():
        return _run_context_suggest(config, repo, args.stem, fs=checkout.fs, require=args.require)

    handlers = {
        "context": handle_context,
        "index": handle_index,
        "meta": handle_meta,
        "training": handle_training,
        "evidence": handle_evidence,
        "host": lambda: {"core": handle_core, "docs": handle_docs, "doctor": handle_doctor}[args.host_verb](),
        "coverage": lambda: {"map": handle_covmap, "gate": handle_covgate}[args.coverage_verb](),
        "ticket": lambda: {"new": handle_new, "lint": handle_lint, "review": handle_review, "order": handle_order, "confirm": handle_verdict, "reject": handle_verdict}[args.ticket_verb](),
        "box": lambda: {"suggest": handle_suggest, "triage": handle_triage, "dismiss": handle_dismiss, "issue": handle_issue}[args.box_verb](),
        "config": lambda: {"init": handle_init_config, "update": handle_update_config, "migrate": handle_migrate_config}[args.config_verb](),
        "provider": lambda: {"install": handle_install, "probe": handle_probe}[args.provider_verb](),
        "prompt": handle_prompt,
        "view": lambda: {"snapshot": handle_watch, "watch": handle_watch, "stats": handle_stats, "status": handle_status, "events": handle_events}[args.view_verb](),
        "roadmap": handle_roadmap,
        "release": lambda: {"bump": handle_release, "publish": handle_publish, "ship": handle_ship}[args.release_verb](),
        "engine": lambda: {
            "stop": handle_control,
            "pause": handle_control,
            "resume": handle_control,
            "kill": handle_control,
            "retro": handle_retro,
            "calibrate": handle_calibrate,
            "serve": handle_serve,
            "run": handle_pipeline,
            "drain": handle_pipeline,
        }[args.engine_verb](),
    }

    try:
        if args.verb == "ticket" and args.ticket_verb in {"confirm", "reject"}:
            isatty, read_input = terminal if terminal is not None else (sys.stdin.isatty, input)
            if not (args.yes or args.extension) and not isatty():
                raise runner.Refusal("verdict requires an interactive terminal", "a human runs this in a terminal: `clutch ticket confirm|reject <stem>`")
        if (
            (args.verb == "coverage" and args.coverage_verb == "gate")
            or (args.verb == "host" and args.host_verb in {"docs", "doctor"})
            or (args.verb == "provider" and args.provider_verb == "install")
            or (args.verb == "config" and args.config_verb in {"init", "migrate"})
            or (args.verb == "box" and args.box_verb == "issue")
            or (args.verb == "ticket" and args.ticket_verb == "new")
        ):
            return handlers[args.verb]()
        config = load_config(args.config, cwd=repo)
        if args.verb == "engine" and args.engine_verb == "drain" and args.detach:
            return handle_detach()
        if args.verb in {"config", "provider", "host", "prompt"}:
            return handlers[args.verb]()
        exec_ = SubprocessExec()
        checkout = runner.Checkout(
            repo=repo,
            config=config,
            env=env,
            exec_=exec_,
            git=Git(
                exec_,
                env={
                    **child_env(env, config),
                    **({"GIT_OPTIONAL_LOCKS": "0"} if (args.verb == "view" and args.view_verb in {"watch", "snapshot"}) or (args.verb == "ticket" and args.ticket_verb == "lint") else {}),
                },
                timeout=GIT_TIMEOUT_S,
                commit_lock=CommitLock(config.state_dir, clock=clock, sleep=asyncio.sleep),
            ),
            journal=Journal(config.state_dir, clock),
            fs=LocalFileSystem(),
            clock=clock,
        )
        if args.verb == "engine" and args.engine_verb in {"serve", "drain", "run"}:
            messages = asyncio.run(hostfiles.stale_core(repo, config, checkout.git))
            if messages:
                raise runner.Refusal("; ".join(messages), f"run clutch host core, then commit the conduct files and retry engine {args.engine_verb}")
        return handlers[args.verb]()
    except UnknownBoxId as e:
        return _fail(args.verb, f"{e} -- name ids that clutch view status lists")
    except (ConfigError, runner.Refusal, LockHeld, CommitLockTimeout, IntakeRefused, JournalCorruption, ProviderSetupError, ExecutableNotFound, hostfiles.MarkerCorruption) as e:
        path = "engine retro" if args.verb == "engine" and args.engine_verb == "retro" else "coverage map" if args.verb == "coverage" and args.coverage_verb == "map" else args.verb
        road = f" -- repair the selected config and retry {path}" if path in {"engine retro", "coverage map"} and isinstance(e, ConfigError) else ""
        return _fail(args.verb, f"{e}{road}")


async def _review(checkout: runner.Checkout, stem: str) -> int:
    from clutch.driver import Driver
    from clutch.tickets import intake

    # Preserve stem, intake, existence and settled refusal precedence before reading main.
    admission = review_admission(stem, admission_facts(()), True, None)
    if admission.outcome == "refuse":
        raise runner.Refusal(admission.message, admission.paved_road)
    pending = await runner.ticket_pending(checkout.git, checkout.repo, stem)
    result = await intake(checkout.repo, checkout.git, checkout.journal, checkout.fs, stems={stem}) if pending else None
    path = checkout.repo / ticket_path(stem)
    intake_decision = result.refused.get(stem) if result else None
    history = checkout.journal.read() if path.is_file() and not intake_decision else ()
    facts = admission_facts(history)
    states = facts.states
    admission = review_admission(stem, facts, path.is_file(), None, intake_decision, pending=pending)
    if admission.outcome == "refuse":
        raise runner.Refusal(admission.message, admission.paved_road)
    text = await checkout.git._run(checkout.repo, "show", f"main:{ticket_path(stem)}")
    try:
        ticket = validate_ticket(stem, text, checkout.repo)
    except TicketInvalid as exc:
        ticket = exc.findings
    admission = review_admission(stem, facts, True, ticket, pending=pending)
    if admission.outcome == "refuse":
        raise runner.Refusal(admission.message, admission.paved_road)
    unmerged = [dep for dep in ticket.depends if states.get(dep) != "merged"]
    session = build_control(checkout).providers
    try:
        llm = await _preflighted_llm(checkout, session)
        driver = Driver.from_config(checkout.config, journal=checkout.journal, llm=llm, env=checkout.env, clock=checkout.clock, sleep=checkout.sleep, fs=checkout.fs)
        verdict = await requisition.review_with_identity(
            driver,
            git=checkout.git,
            config=checkout.config,
            history=history,
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
                "input_identity": verdict.input_identity,
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


async def _submit_engine(checkout, exc, verb, *, stem=None, extension=False, ids=None, reason=None):
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
    if verb == "triage":
        request = control.TriageRequest(uuid4().hex, lifecycle, verb, list(ids), None, "operator")
    elif stem is not None:
        request = control.AdmissionRequest(uuid4().hex, lifecycle, verb, stem, None, "extension" if extension else "operator", operator_reason=reason)
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
                raise runner.Refusal(str(exc), "restore journal readability from backup and retry engine retro") from None
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
    from clutch.providers import judge_independence_finding

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
        facts = admission_facts(events)
        pending = _pending(checkout.repo, _porcelain(await checkout.git.status_porcelain(checkout.repo)))
        for stem in selected:
            rel = ticket_path(stem)
            path = checkout.repo / rel
            # Check existence before the stem grammar, without following an escaped path.
            inside = Path(stem).name == stem and stem not in {".", ".."} and path.resolve().is_relative_to(root.resolve())
            admission = lint_admission(stem, facts, inside and path.is_file())
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
            judge_finding = None
            try:
                if findings:
                    raise TicketInvalid(findings)
                ticket = validate_ticket(stem, text, checkout.repo)
                judge_finding = judge_independence_finding(checkout.config) if ticket.frontmatter.kind == "graphics" else None
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
            if judge_finding:
                print(f"{rel}: {judge_finding}")
            if findings or ceiling_finding or judge_finding:
                exit_code = max(exit_code, 1)
            else:
                valid += 1
    except (OSError, UnicodeError, GitError) as exc:
        print(f"{root}: {exc} (restore ticket and repository readability, then retry clutch ticket lint)")
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
            kind = read_tolerant((checkout.repo / ticket_path(stem)).read_text()).frontmatter.get("kind")
            if kind in KINDS:
                kinds[stem] = kind
        except OSError, UnicodeError:
            pass
    checks = {}
    for e in events:
        if e.type == EventType.EFFECT_COMPLETION and e.ticket and re.fullmatch(r"ticket-plane/[^/]+/\d+/checks", e.key or "") and start <= datetime.fromisoformat(e.ts) <= now:
            text = await checkout.git._run(checkout.repo, "show", f"{e.body['result']['commit']}:{artifact_path(e.ticket, CHECKS_FILE)}")
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
        overdue=overdue(events, checkout.config).values(),
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


async def _verdict(checkout, stem, verb, read_input, yes, extension, *, reason=None):
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
        return await runner.verdict(stem, checkout, kill=verb == "reject", extension=extension, **({"reason": reason} if reason is not None else {}))
    except LockHeld as exc:
        request = await _submit_engine(checkout, exc, verb, stem=stem, extension=extension, reason=reason)
    print(f"{verb} submitted: {request.request_id} -- `clutch view status` shows the outcome")
    return 0


def _order(checkout, stem, priority, runs_before):
    if findings := stem_findings(stem):
        raise runner.Refusal(findings[0].message, findings[0].paved_road)
    if priority is None and runs_before is None:
        raise runner.Refusal("no ordering option supplied", "supply --priority or --runs-before")
    path = checkout.repo / ticket_path(stem)
    exists = path.is_file()
    events = checkout.journal.read() if exists else ()
    facts = admission_facts(events)
    state = facts.states.get(stem)
    holder = observe.lock_holder(checkout.config.state_dir) if state == "running" and stem in facts.orphans else None
    admission = order_admission(stem, facts, exists, holder)
    if admission.outcome == "refuse":
        raise runner.Refusal(admission.message, admission.paved_road)
    text = path.read_bytes().decode()
    try:
        try:
            changed = order(text, priority=priority, runs_before=runs_before)
        except ValueError, StopIteration:
            validate_ticket(stem, text, checkout.repo)
            raise runner.Refusal("ticket ordering fields cannot be edited", "use ordinary priority and section headings, then retry ticket order") from None
        ticket = validate_ticket(stem, changed, checkout.repo)
        if priority is not None and ticket.frontmatter.priority != priority:
            raise runner.Refusal("priority line cannot be edited", "write priority as a plain `priority: P2` line, then retry ticket order")
    except TicketInvalid as exc:
        admission = order_admission(stem, facts, exists, holder, exc.findings)
        raise runner.Refusal(admission.message, admission.paved_road) from None
    checkout.fs.write(path, changed.encode())
    fields = ([f"priority: {priority}"] if priority is not None else []) + ([f"runs before: {', '.join(runs_before) or '(cleared)'}"] if runs_before is not None else [])
    print(f"ordered {stem}: {'; '.join(fields)}")
    return 0


def _new(repo: Path, stem: str, kind: str = "feature", evidence: Sequence[str] = (), reference: Sequence[str] = (), inputs: Sequence[str] = ()) -> int:
    """Author a ticket and its evidence outside the lock fence."""
    if kind == "bug" and not evidence:
        raise runner.Refusal(
            "a bug ticket needs its evidence first", f"save the observed failure (output, log excerpt, or captured command output) to a file, then rerun ticket new {stem} --kind bug --evidence <file>"
        )
    if kind != "bug" and evidence:
        raise runner.Refusal("evidence is for bug tickets", "omit --evidence or choose --kind bug")
    if kind != "graphics" and (reference or inputs):
        raise runner.Refusal("reference and input files are for graphics tickets", "omit --reference and --input or choose --kind graphics")
    sources = [repo / path for path in (*evidence, *reference, *inputs)]
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
        directory = "evidence" if kind == "bug" else "reference"
        fs.write(repo / "tickets" / stem / directory / source.name, source.read_bytes())
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
        print(f"fill these before `engine run {stem}`:")
        for f in findings:
            print(f"- {f.message} ({f.paved_road})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
