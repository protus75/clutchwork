"""Label image cases independently and measure visual judge agreement."""

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, ValidationError

from clutch import visual
from clutch.config import Candidate, Route, load_config
from clutch.driver import Driver, LlmStage
from clutch.git import Git
from clutch.journal import EventType, Journal
from clutch.lockfile import CommitLock, Lockfile
from clutch.policy import VISUAL_BASELINE_SIGNAL, visual_identity
from clutch.providers import ProviderLLM, ProviderSession
from clutch.runner import call_timeout
from clutch.seams import LocalFileSystem, SubprocessExec
from clutch.specs import load_spec, render
from clutch.timers import Timers
from eval.harness import MIN_CATCH_RATE

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "eval" / "visual"
SPECS = ROOT / "clutch" / "specs"


class Panel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    provider: str
    model: str


class Label(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    verdict: Literal["accept", "reject"]
    rows: dict[str, Literal["pass", "fail"]]


class CaseData(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    mode: Literal["command", "generate"]
    visual_criteria: list[str]
    inputs: list[str]
    candidate: str
    panel: Panel
    label: Label | None = None


@dataclass(frozen=True)
class Case:
    directory: Path
    data: CaseData


def load_cases(root: Path, judge_provider: str, *, labelled_only: bool = True) -> list[Case]:
    cases = []
    if not root.exists():
        return cases
    for directory in sorted(p for p in root.iterdir() if p.is_dir()):
        try:
            data = CaseData.model_validate_json((directory / "case.json").read_text())
            ids = visual.rubric_ids(data.visual_criteria, data.mode)
            if not ids or len(ids) != len(set(ids)) or any(not item.strip() for item in ids):
                raise ValueError("rubric ids must be nonblank and unique")
            if not data.panel.provider.strip() or not data.panel.model.strip() or data.panel.provider == judge_provider:
                raise ValueError("panel provider must differ from the judge and panel identity must be nonblank")
            if data.label is not None and set(data.label.rows) != set(ids):
                raise ValueError("label must contain exactly the rubric ids")
            for name in [*data.inputs, data.candidate]:
                path = (directory / name).resolve()
                if not name or not path.is_relative_to(directory.resolve()) or not path.is_file():
                    raise ValueError(f"image path {name!r} must be a file inside the case")
            if data.label is not None or not labelled_only:
                cases.append(Case(directory, data))
        except (OSError, ValidationError, ValueError) as exc:
            raise ValueError(f"case {directory.name}: {exc}") from exc
    return cases


def agreement(results: Sequence[tuple[Case, visual.Reply | None]]) -> dict:
    count = len(results)
    overall = sum(reply is not None and reply.verdict == case.data.label.verdict for case, reply in results) / count if count else 0.0
    rows: dict[str, list[bool]] = {}
    for case, reply in results:
        actual = {row.id: row.verdict for row in reply.rows} if reply else {}
        for row_id, expected in case.data.label.rows.items():
            rows.setdefault(row_id, []).append(actual.get(row_id) == expected)
    return {
        "case_count": count,
        "overall": overall,
        "rows": {key: sum(values) / len(values) for key, values in rows.items()},
        "verdict": "GO" if count >= 20 and overall >= MIN_CATCH_RATE else "NO_GO",
    }


def _stage(case, spec):
    ids = visual.rubric_ids(case.data.visual_criteria, case.data.mode)
    material = {
        "ticket": "",
        "generator_prompt": "",
        "images": "\n".join(str(case.directory / p) for p in case.data.inputs),
        "candidates": str(case.directory / case.data.candidate),
        "scores": "not available",
        "rubric": "\n".join(ids),
    }
    return LlmStage(surface="review_visual", emits=visual.Reply, gates=[], render=lambda _, findings: render(spec, material))


async def _judge(driver, case, spec, *, attempt, samples, workspace, member):
    replies = []
    ids = visual.rubric_ids(case.data.visual_criteria, case.data.mode)
    for sample in range(samples):
        result = await driver.run(
            _stage(case, spec),
            None,
            ticket=f"visual-baseline-{case.directory.name}",
            attempt=attempt,
            workspace=workspace,
            tier=spec.meta.tier,
            effort=spec.meta.effort,
            stuck_budget=1200.0,
            expected_budget="eval",
            scope_fence=(),
            key_scope=f"sample{sample}",
            kind="graphics",
        )
        if result.outcome != "ok" or result.artifact is None or (result.cost.provider, result.cost.model) != (member["provider"], member["model"]):
            return None
        try:
            replies.append(visual.parse_reply(result.artifact.model_dump_json(), ids))
        except ValueError:
            return None
    return visual.majority(replies)


async def run_baseline(*, config, driver, journal, cases, report_path, specs_dir=SPECS, workspace=ROOT):
    spec = load_spec((specs_dir / "review_visual.md").read_text())
    identity = visual_identity(config, specs_dir)
    judge = identity["review_visual"]["rows"][spec.meta.tier]["provider"]
    if any(case.data.panel.provider == judge or case.data.label is None for case in cases):
        raise ValueError("labelled cases must have an independent panel")
    attempt = 1 + sum(event.body.get("signal") == VISUAL_BASELINE_SIGNAL for event in journal.read())
    results = [
        (case, await _judge(driver, case, spec, attempt=attempt, samples=config.graphics.judge_samples, workspace=workspace, member=identity["review_visual"]["rows"][spec.meta.tier]))
        for case in cases
    ]
    report = agreement(results)
    body = {"signal": VISUAL_BASELINE_SIGNAL, "verdict": report["verdict"], "identity": identity, "overall": report["overall"], "case_count": report["case_count"]}
    journal.append(EventType.SIGNAL, body)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


async def _execute(config, command, env, *, root=CASES, report_path=ROOT / "eval" / "visual_report.json"):
    def clock():
        return datetime.now(UTC)

    exec_ = SubprocessExec()
    instance = await Git(exec_, env=env, timeout=30, commit_lock=CommitLock(config.state_dir, clock=clock, sleep=asyncio.sleep)).describe(ROOT)
    lock = Lockfile(config.state_dir, verb="eval", instance_id=instance, clock=clock)
    lock.acquire()
    session = None
    try:
        journal = Journal(config.state_dir, clock)
        timers = Timers(journal=journal, clock=clock, sleep=asyncio.sleep)
        timers.reconstruct()
        timers.fire_due()
        session = ProviderSession(config, journal=journal, clock=clock, sleep=asyncio.sleep, timers=timers)
        spec = load_spec((SPECS / "review_visual.md").read_text())
        identity = visual_identity(config)
        judge = identity["review_visual"]["rows"][spec.meta.tier]["provider"]
        cases = load_cases(root, judge, labelled_only=command == "run")
        if command == "run" and not cases:
            return await run_baseline(config=config, driver=None, journal=journal, cases=[], report_path=report_path)
        for case in cases if command == "label" else [None]:
            chosen = config
            if case is not None:
                if case.data.label is not None:
                    continue
                chosen = config.model_copy(
                    update={"routing": [Route(tier=spec.meta.tier, surface="review_visual", candidates=[Candidate(provider=case.data.panel.provider, model=case.data.panel.model)])]}
                )
            llm = ProviderLLM(chosen, exec_=exec_, fs=LocalFileSystem(), env=env, cwd=ROOT, timeout=call_timeout(config), session=session)
            if problems := await llm.preflight():
                raise ValueError("; ".join(problems))
            driver = Driver.from_config(chosen, journal=journal, llm=llm, env=env, clock=clock, sleep=asyncio.sleep)
            if case is None:
                return await run_baseline(config=config, driver=driver, journal=journal, cases=cases, report_path=report_path)
            reply = await _judge(driver, case, spec, attempt=1 + len(journal.read()), samples=1, workspace=ROOT, member=case.data.panel.model_dump())
            if reply is None or reply.verdict == "unsure" or any(row.verdict == "unsure" for row in reply.rows):
                raise ValueError(f"case {case.directory.name}: panel did not produce a definite label")
            data = case.data.model_dump(mode="json")
            data["label"] = {"verdict": reply.verdict, "rows": {row.id: row.verdict for row in reply.rows}}
            (case.directory / "case.json").write_text(json.dumps(data, indent=2) + "\n")
    finally:
        try:
            if session is not None:
                await session.close()
        finally:
            lock.release()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m eval.visual_harness")
    parser.add_argument("command", choices=("label", "run"))
    args = parser.parse_args(argv)
    result = asyncio.run(_execute(load_config(None, cwd=ROOT), args.command, dict(os.environ)))
    if result is not None:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
