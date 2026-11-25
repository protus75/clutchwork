"""Help topics for the operator surfaces."""

import re
from pathlib import Path

import clutch

DOCS = Path(clutch.__file__).parent / "docs"
TOPICS = {}


def _add(kind, rows, heading, doc="docs/how-clutch-works.md"):
    for name, what in rows.items():
        TOPICS[f"{kind}.{name}"] = dict(what=what, doc=doc, heading=heading)


_add(
    "view",
    {
        "clutch.details": "Shows details of the selected item.",
        "clutch.steps": "Shows recent engine steps.",
        "clutch.tickets": "Shows tickets and their dependencies.",
        "clutch.box": "Shows Suggestion Box messages.",
        "clutch.stats": "Shows health and efficiency statistics.",
        "clutch.dashboard": "Shows the ClutchWork dashboard.",
        "clutch.help": "Shows help topics and documentation links.",
        "clutch.lifecycle": "Shows the ticket lifecycle diagram.",
    },
    "VS Code extension",
    "host-contract.md",
)

_commands = {
    "clutch.askPrompt": "Open a prompt chosen from every engine and host prompt.",
    "clutch.askDrainLoop": "Open a prompt about supervising the drain loop.",
    "clutch.help": "Browse clutch help topics.",
    "clutch.refresh": "Refresh the displayed state.",
    "clutch.steps.copySession": "Copy the model session id of the selected step.",
    "clutch.ticket.copySession": "Copy the model session id of the running ticket.",
    "clutch.ticket.copyStem": "Copy the selected ticket's stem.",
    "clutch.ticket.open": "Open the selected ticket.",
    "clutch.ticket.askDiagnose": "Open a prompt to diagnose the selected ticket.",
    "clutch.ticket.askReview": "Open a prompt to review the selected ticket.",
    "clutch.openSettings": "Open clutch settings.",
    "clutch.lifecycle": "Open the ticket lifecycle diagram.",
    "clutch.box.open": "Open the selected message file.",
    "clutch.box.link": "Open the selected message's linked record.",
    "clutch.box.discuss": "Open a prompt to discuss selected messages.",
    "clutch.engine": "Choose an engine action.",
    "clutch.updateProvider": "Choose a provider CLI to update.",
    "clutch.openConfig": "Open the host configuration.",
    "clutch.ticket.askDrafts": "Open a prompt to assess drafts.",
}
_add("command", _commands, "VS Code extension", "host-contract.md")
COMMANDS = {name: f"command.{name}" for name in _commands}
COMMANDS.update(
    {
        "clutch.ticket.review": "verb.review",
        "clutch.ticket.lint": "verb.lint",
        "clutch.ticket.run": "verb.run",
        "clutch.ticket.confirm": "verb.confirm",
        "clutch.ticket.reject": "verb.reject",
        "clutch.ticket.priority": "verb.order",
        "clutch.ticket.runsBefore": "verb.order",
        "clutch.box.triage": "verb.triage",
        "clutch.box.dismiss": "verb.dismiss",
        "clutch.bulkTriage": "verb.triage",
        "clutch.playDrain": "verb.drain",
        "clutch.playServe": "verb.serve",
        "clutch.stopRunning": "verb.stop",
    }
)
for _verb in ("drain", "serve", "stop", "kill", "status", "retro", "review", "lint", "run", "confirm", "reject", "order", "triage", "dismiss"):
    TOPICS[f"verb.{_verb}"] = dict(
        doc="host-running.md",
        verb=f"ticket {_verb}"
        if _verb in {"review", "lint", "order", "confirm", "reject"}
        else f"engine {_verb}"
        if _verb in {"drain", "serve", "stop", "run", "kill", "retro"}
        else f"box {_verb}"
        if _verb in {"triage", "dismiss"}
        else f"view {_verb}",
    )

_add(
    "verdict",
    {"decisions": "Shows verdict requests that were not applied."},
    "7.3 Control",
)
_add(
    "section",
    {
        "blocked": "Tickets in this section cannot currently run.",
        "queued": "Tickets in this section are ordered for a future run.",
        "running": "Tickets in this section are currently running.",
        "merged": "This section shows the most recently settled tickets, up to snapshot_merged_limit.",
    },
    "7.1 `drain`",
)
_add(
    "status",
    {
        "invalid": "The ticket cannot be parsed or validated.",
        "new": "The ticket awaits intake.",
        "draft": "The draft awaits confirmation.",
        "held_change": "The ticket is held until its content changes.",
        "held_operator": "The ticket awaits an operator verdict.",
        "waits_on": "The ticket waits for dependencies to settle.",
        "not_eligible": "The ticket is not eligible to run.",
        "interrupted": "The engine stopped during the ticket's run.",
        "upgrade_hold": "The ticket is held for an engine upgrade until serve re-execs on the new code.",
        "retry_pending": "The ticket is waiting for another attempt.",
        "after": "The ticket is ordered after other tickets.",
        "ready": "The ticket is ready for dispatch.",
        "slot_overlap": "The ticket is ready but its scope fence overlaps a running or barrier ticket, so it waits for a free slot.",
        "merge_wait": "The ticket is ready but dispatch waits until finished tickets merge (`scheduler.max_unmerged`).",
        "running": "The ticket is running.",
        "merged": "The ticket's change has merged.",
        "already_satisfied": "The ticket settled without a change.",
    },
    "7.1 `drain`",
)
_add(
    "step",
    {
        name: f"Records the {name.replace('_', ' ')} event."
        for name in (
            "acceptance",
            "requisition_review",
            "implement",
            "check",
            "merge",
            "review",
            "review_visual",
            "diagnose",
            "rework",
            "retro",
            "triage",
            "author",
            "preflight",
            "retro_check",
            "stage",
            "engine_start",
            "engine_stop",
            "engine_lost",
        )
    },
    "4. A ticket's run",
)
_add(
    "step",
    {"resolve": "Resolves bounded text conflicts in serve merge admission."},
    "7.2.1 Merge queue (serve only)",
)

_add(
    "step",
    {"meta": "Fills file metadata with a read-only model."},
    "2. Commands",
)

_add(
    "box",
    {
        "suggestion": "A suggestion proposes work or an idea.",
        "failure_report": "A failure report records a failed dependency or run.",
        "override_report": "An override report records an override.",
        "retro_finding": "A retro finding proposes a follow-up from a retro.",
        "roadmap_row": "A roadmap row asks Author for the ticket one docs/roadmap.md row describes.",
        "bug_report": "A bug report records a host-reported problem.",
    },
    "9.1 Messages",
)
_add(
    "boxOutcome",
    {
        "pending": "The message awaits triage.",
        "reopened": "The message has reopened after recurrence.",
        "author": "Triage authored a ticket for the message.",
        "tombstone": "Triage found the message already covered.",
        "declined": "Triage recorded a decision to decline the message.",
    },
    "9.2 Triage",
)
_add(
    "stat",
    {
        "window": "Describes the selected statistics window.",
        "throughput": "Summarizes intake and settled tickets.",
        "durations": "Summarizes stage and attempt durations.",
        "verification": "Summarizes verification command durations.",
        "cycles": "Summarizes attempts and review cycles.",
        "ladder": "Summarizes escalations and their outcomes.",
        "failures": "Summarizes terminal failures and diagnoses.",
        "holds": "Summarizes holds and operator keeps.",
        "usage": "Summarizes token usage and calls per provider; tokens are never summed across providers because they are not the same unit.",
    },
    "2.1 Verbs",
)
_add(
    "lock",
    {"engine": "The engine lock allows one writer per host.", "commit": "The commit lock serializes git index writes and commits."},
    "10.1 Files",
)
TOPICS["priority"] = dict(what="Priority helps order eligible tickets.", doc="docs/how-clutch-works.md", heading="7.1 `drain`")


def topic_text(key):
    return TOPICS[key]["what"]


def _slug(heading):
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def help_map(read, repo_url):
    result = {}
    cache = {}
    for key, entry in TOPICS.items():
        doc = entry["doc"]
        if doc.startswith("docs/"):
            link = {"label": entry["heading"], "url": f"{repo_url.rstrip('/')}/blob/main/{doc}#{_slug(entry['heading'])}"}
        else:
            path = DOCS / doc
            if path not in cache:
                cache[path] = read(path).splitlines()
            lines = cache[path]
            if "verb" in entry:
                verb = entry["verb"]
                line = next((i for i, row in enumerate(lines) if row.startswith(f"| `{verb}` |")), None)
                if line is None:
                    raise LookupError(f"{key}: verb {verb} missing from {path}; restore the row or update clutch/help.py")
                what = lines[line].split("|")[3].strip().replace("`", "")
                link = {"label": f"{verb} in the run guide", "path": str(path), "line": line}
            else:
                heading = entry["heading"]
                line = next((i for i, row in enumerate(lines) if re.fullmatch(r"#+\s+" + re.escape(heading), row)), None)
                if line is None:
                    raise LookupError(f"{key}: heading {heading} missing from {path}; restore it or update clutch/help.py")
                link = {"label": heading, "path": str(path), "line": line}
        if "verb" not in entry:
            what = entry["what"]
        result[key] = {"what": what, "text": what, "link": link}
    return result


def help_pick(help):
    items = []
    previous = None
    for key, entry in help.items():
        kind, _, label = key.partition(".")
        if kind != previous:
            items.append({"kind": "separator", "label": kind})
            previous = kind
        items.append({"label": label or kind, "description": entry["link"]["label"], "detail": entry["what"], "topic": key})
    items.append({"label": "Settings", "detail": "Open clutch settings.", "command": "clutch.openSettings"})
    return items
