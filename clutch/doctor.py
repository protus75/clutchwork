"""Read-only mechanical setup checks."""

import fcntl
from dataclasses import dataclass

from clutch import antigravity
from clutch.config import load_config
from clutch.evidence.store import EvidenceStore, size_warning
from clutch.git import Git
from clutch.hostfiles import stale_core
from clutch.journal import Journal
from clutch.lockfile import CommitLock, LockHeld, _read_holder
from clutch.providers import judge_independence_finding, panel_slots_finding
from clutch.seams import LocalFileSystem
from clutch.status import overdue


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str
    warn: bool = False


def inspect_lock(state_dir):
    """Probe an existing inode without creating it or publishing writer identity."""
    path = state_dir / "clutch.lock"
    try:
        stream = path.open("rb")
    except FileNotFoundError:
        return "no writer lock exists"
    with stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise LockHeld(path, _read_holder(stream.fileno())) from None
    return "writer lock is available"


async def check(*, repo, config_path, env, exec_, clock, sleep, in_venv):
    results = []

    def row(name, passed, detail):
        results.append(Check(name, passed, " ".join(str(detail).split())))

    row("venv", in_venv, "active Python venv" if in_venv else "no active Python venv; run `uv run clutch host doctor`")
    config = None
    try:
        config = load_config(config_path, cwd=repo)
        row("config", True, "config schema is valid")
    except Exception as exc:
        row("config", False, f"{exc}; repair the selected config and rerun host doctor")
    if config is None:
        row("git", False, "not checked: config did not load; fix the config and rerun host doctor")
    else:
        git = Git(exec_, env={"PATH": env.get("PATH", "")}, timeout=30.0, commit_lock=CommitLock(config.state_dir, clock=clock, sleep=sleep))
        try:
            out = await git._run(repo, "--version")
            row("git", True, out.strip())
        except Exception as exc:
            row("git", False, f"{exc}; install git or fix PATH")
    for name in ("lock", "journal"):
        if config is None:
            row(name, False, "state directory unavailable; repair the selected config and rerun host doctor")
            continue
        try:
            if name == "journal":
                events = Journal(config.state_dir, clock).read()
            detail = inspect_lock(config.state_dir) if name == "lock" else f"readable history ({len(events)} events)"
            row(name, True, detail)
            if name == "journal":
                results.extend(Check(name, True, line, warn=True) for name, line in overdue(events, config).items())
        except Exception as exc:
            row(
                name,
                False,
                f"{exc}; " + ("restore journal readability from backup and rerun host doctor" if name == "journal" else "wait for the writer to exit or stop it; never delete the lockfile"),
            )
    if config is None:
        row("core", False, "state directory unavailable; repair the selected config and rerun host doctor")
    else:
        try:
            messages = await stale_core(repo, config, git)
            row("core", not messages, "; ".join(messages) if messages else "routed conduct files are current")
        except Exception as exc:
            row("core", False, f"{exc}; install git or fix PATH, then rerun host doctor")
    if config is not None:
        fs = LocalFileSystem()
        store = EvidenceStore(config.state_dir, fs, fs.read_bytes, fs.size, lambda text: text)
        if message := size_warning(store, config.evidence.warn_gb):
            results.append(Check("evidence", True, message, warn=True))
    if config is not None and config.scheduler.parallel.enabled:
        route = next((r for r in config.routing if r.tier == config.routing_default_tier and r.surface == "implement"), None)
        if route is not None:
            provider = next(p for p in config.providers if p.name == route.candidates[0].provider)
            max_runs = config.scheduler.parallel.max_runs
            if max_runs > provider.limits.concurrency:
                row("parallel", False, f"max_runs {max_runs} exceeds provider {provider.name} limits.concurrency {provider.limits.concurrency}; lower max_runs or raise limits.concurrency")
    if config is not None and (finding := judge_independence_finding(config)):
        row("judge", False, finding)
    if config is not None and (finding := panel_slots_finding(config)):
        row("panel", False, finding)
    if finding := antigravity.doctor_finding(antigravity.default_plugin_dir(env)):
        results.append(Check("antigravity", True, finding, warn=True))
    return results


def render(results):
    return "\n".join(["doctor: ok" if all(r.passed for r in results) else "doctor: failed", *(f"{'WARN' if r.warn else 'PASS' if r.passed else 'FAIL'} {r.name}: {r.detail}" for r in results)]) + "\n"
