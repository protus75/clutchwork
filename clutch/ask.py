"""Render engine-owned operator prompts."""

from pathlib import Path
from string import Template

import yaml

from clutch import specs
from clutch.config import Config
from clutch.runner import SPECS_DIR
from clutch.tickets import split_frontmatter, stem_findings, ticket_path

KINDS = ("diagnose", "running", "review", "box", "drafts", "drain-loop", "plan-ticket-drain", "plan-ticket-serve", "author", "roadmap")


DESCRIPTIONS = {
    "diagnose": "Diagnose a ticket, selecting the running prompt when it is live.",
    "running": "Inspect a running ticket.",
    "review": "Audit a ticket against merged and confirmed work.",
    "box": "Discuss named Suggestion Box messages.",
    "drafts": "Assess committed drafts awaiting a verdict.",
    "drain-loop": "Print the supervising drain-loop prompt.",
    "plan-ticket-drain": "Print the unattended roadmap kickoff prompt.",
    "plan-ticket-serve": "Print the unattended roadmap serve kickoff prompt.",
    "author": "Author a ticket from its roadmap row or request.",
    "roadmap": "Print the roadmap creation and maintenance prompt.",
}
TAKES = {kind: ("box" if kind == "box" else "none" if kind in ("drafts", "drain-loop", "plan-ticket-drain", "plan-ticket-serve", "roadmap") else "stem") for kind in KINDS}


def render(kind: str, stem: str, config: Config, repo: Path) -> str:
    if kind not in KINDS:
        raise ValueError(f"unknown prompt kind: {kind}")
    state = config.state_dir.resolve()
    root = repo.resolve()
    state_dir = state.relative_to(root) if state.is_relative_to(root) else state
    if kind == "box":
        from clutch.box import BOX_DIR, Box
        from clutch.seams import LocalFileSystem

        box = Box(state / BOX_DIR, LocalFileSystem())
        messages = [box.get(id) for id in stem]
        paths = "\n".join(f"- {m.id}: {state_dir / BOX_DIR / box.path(m).name}" for m in messages)
        template = Template((SPECS_DIR / "ask" / "box.md").read_text())
        result = template.substitute(messages=paths)
    elif kind == "roadmap":
        facet = (SPECS_DIR / "doc" / "facets" / "type" / "roadmap.md").read_text()
        template = Template((SPECS_DIR / "ask" / "roadmap.md").read_text())
        result = template.substitute(facet=facet)
    elif kind in ("drain-loop", "plan-ticket-drain", "plan-ticket-serve"):
        template = Template((SPECS_DIR / "ask" / f"{kind}.md").read_text())
        result = template.substitute(state_dir=str(state_dir))
    elif kind == "drafts":
        paths = "\n".join(f"- {item}: {ticket_path(item)}" for item in stem)
        template = Template((SPECS_DIR / "ask" / "drafts.md").read_text())
        result = template.substitute(tickets=paths, state_dir=str(state_dir))
    else:
        template = Template((SPECS_DIR / "ask" / f"{kind}.md").read_text())
        result = template.substitute(stem=stem, ticket=str(ticket_path(stem)), state_dir=str(state_dir))
    if config.ask_notes is not None:
        result += f"\n{specs.data_open('host_notes')}\n{specs.quote_payload(config.ask_notes)}\n{specs.data_close('host_notes')}\n"
    return result


def _host_file(path: Path):
    try:
        if findings := stem_findings(path.stem):
            raise ValueError(findings[0].message)
        split = split_frontmatter(path.read_text(encoding="utf-8"))
        if split is None:
            raise ValueError("missing YAML frontmatter")
        metadata = yaml.safe_load(split[0])
        if not isinstance(metadata, dict) or set(metadata) != {"description", "takes"}:
            raise ValueError("frontmatter requires exactly description and takes")
        description, takes = metadata["description"], metadata["takes"]
        if not isinstance(description, str) or not description.strip() or "\n" in description or "\r" in description:
            raise ValueError("description must be non-empty and one line")
        if takes not in ("none", "stem"):
            raise ValueError("takes must be none or stem")
        values = {"state_dir": "state"}
        if takes == "stem":
            values.update(stem="example", ticket="tickets/example/ticket.md")
        Template(split[1]).substitute(values)
        return metadata, split[1]
    except (OSError, UnicodeError, yaml.YAMLError, ValueError, KeyError, TypeError, RecursionError) as exc:
        raise ValueError(f"{path}: {exc}") from None


def catalog(config: Config, repo: Path):
    entries = [dict(name=kind, argv=["prompt", kind], takes=TAKES[kind], description=DESCRIPTIONS[kind], source="engine") for kind in KINDS]
    problems = []
    if config.prompts_dir is not None:
        for path in sorted(config.prompts_dir.glob("*.md")):
            try:
                metadata, _ = _host_file(path)
                entries.append(dict(name=path.stem, argv=["prompt", "host", path.stem], takes=metadata["takes"], description=metadata["description"], source="host"))
            except ValueError as exc:
                problems.append((path, str(exc)))
    return entries, problems


def render_host(name: str, stem: str, config: Config, repo: Path) -> str:
    if config.prompts_dir is None or stem_findings(name):
        raise ValueError(f"unknown host prompt: {name}")
    path = config.prompts_dir / f"{name}.md"
    metadata, body = _host_file(path)
    state = config.state_dir.resolve()
    root = repo.resolve()
    state_dir = state.relative_to(root) if state.is_relative_to(root) else state
    values = {"state_dir": str(state_dir)}
    if metadata["takes"] == "stem":
        values.update(stem=stem, ticket=str(ticket_path(stem)))
    result = Template(body).substitute(values)
    if config.ask_notes is not None:
        result += f"\n{specs.data_open('host_notes')}\n{specs.quote_payload(config.ask_notes)}\n{specs.data_close('host_notes')}\n"
    return result


def resolve_prompt(kind, stems=(), *, name=None, config, repo, running_stems, draft_stems):
    from clutch.runner import Refusal

    if kind == "list":
        entries, problems = catalog(config, repo)
        return "", {"entries": entries, "problems": [(str(p), msg) for p, msg in problems]}
    if kind == "host":
        if config.prompts_dir is None:
            raise Refusal("prompts_dir is unset", "set prompts_dir in config.yaml", code="no_prompts_dir")
        entries, problems = catalog(config, repo)
        path = config.prompts_dir / f"{name}.md"
        problem = next((message for p, message in problems if p == path), None)
        if problem:
            raise Refusal(f"{path}: {problem}", "repair the host prompt file", code="invalid_prompt")
        entry = next((e for e in entries if e["source"] == "host" and e["name"] == name), None)
        if entry is None:
            raise Refusal(f"unknown host prompt {name!r}", "run clutch prompt list and choose a valid host prompt", code="unknown_prompt")
        if len(stems) != (1 if entry["takes"] == "stem" else 0):
            raise Refusal(f"host prompt {name} takes {entry['takes']}", "supply exactly one ticket stem" if entry["takes"] == "stem" else "omit the stem", code="invalid_arguments")
        stem = stems[0] if stems else ""
        if stem:
            _validate_prompt_stem(stem, repo, True)
        try:
            return render_host(name, stem, config, repo), None
        except ValueError as exc:
            raise Refusal(str(exc), "repair the host prompt file", code="invalid_prompt") from None
    if kind not in KINDS:
        raise Refusal(f"unknown prompt kind: {kind}", "run clutch prompt list", code="unknown_prompt")
    if TAKES[kind] == "none":
        if stems:
            raise Refusal(f"{kind} takes no stem" if kind != "drafts" else "drafts prompt takes no stems", f"run clutch prompt {kind} with no stems", code="invalid_arguments")
        if kind == "drafts":
            stems = draft_stems()
            if not stems:
                raise Refusal("no draft tickets await confirm or reject", "run clutch box triage, or author a ticket with clutch ticket new", code="no_drafts")
            return render(kind, stems, config, repo), None
        return render(kind, "", config, repo), None
    if kind == "box":
        if not stems:
            raise Refusal("box prompt requires ids", "name at least one box id", code="invalid_arguments")
        return render(kind, stems, config, repo), None
    if len(stems) != 1:
        raise Refusal("ticket prompt requires exactly one stem", "name one ticket stem", code="invalid_arguments")
    stem = stems[0]
    _validate_prompt_stem(stem, repo, kind != "author")
    selected = "running" if kind == "diagnose" and stem in running_stems() else kind
    return render(selected, stem, config, repo), None


def _validate_prompt_stem(stem, repo, require_ticket):
    from clutch.runner import Refusal

    if findings := stem_findings(stem):
        raise Refusal(findings[0].message, findings[0].paved_road, code="invalid_stem")
    if require_ticket and not (repo / ticket_path(stem)).is_file():
        raise Refusal(f"{ticket_path(stem)} does not exist", f"author it with clutch ticket new {stem}", code="missing_ticket")
