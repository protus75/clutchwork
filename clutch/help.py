"""Help topics for the operator surfaces."""

import re
from pathlib import Path

import clutch

DOCS = Path(clutch.__file__).parent / "docs"
TOPICS = {}


def _add(kind, rows, heading, before, after, doc="docs/how-clutch-works.md"):
    for name, what in rows.items():
        TOPICS[f"{kind}.{name}"] = dict(what=what, before=before, after=after, doc=doc, heading=heading)


_add(
    "view",
    {
        "clutch.details": "Shows details of the selected item.",
        "clutch.steps": "Shows recent engine steps.",
        "clutch.tickets": "Shows tickets and their dependencies.",
        "clutch.box": "Shows Suggestion Box messages.",
        "clutch.stats": "Shows health and efficiency statistics.",
    },
    "VS Code extension",
    "Open a clutch workspace.",
    "Select an item or action.",
    "host-contract.md",
)

_commands = {
    "clutch.askDrainLoop": "Open a prompt about supervising the drain loop.",
    "clutch.help": "Browse clutch help topics.",
    "clutch.refresh": "Refresh the displayed state.",
    "clutch.ticket.open": "Open the selected ticket.",
    "clutch.ticket.askDiagnose": "Open a prompt to diagnose the selected ticket.",
    "clutch.ticket.askReview": "Open a prompt to review the selected ticket.",
    "clutch.openSettings": "Open clutch settings.",
    "clutch.lifecycle": "Open the ticket lifecycle diagram.",
    "clutch.box.open": "Open the selected message file.",
    "clutch.box.link": "Open the selected message's linked record.",
    "clutch.box.discuss": "Open a prompt to discuss selected messages.",
    "clutch.engine": "Choose an engine action.",
    "clutch.openConfig": "Open the host configuration.",
    "clutch.ticket.askDrafts": "Open a prompt to assess drafts.",
}
_add("command", _commands, "VS Code extension", "Open a clutch workspace.", "Use the selected action.", "host-contract.md")
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
    TOPICS[f"verb.{_verb}"] = dict(before="Choose the action for the current state.", after="Inspect the result.", doc="host-running.md", verb=_verb)

_add(
    "verdict",
    {"decisions": "Shows verdict requests that were not applied."},
    "7.3 Control",
    "A confirm or reject request is published.",
    "Fix the reason and run confirm or reject again for the stem.",
)
_add(
    "section",
    {
        "blocked": "Tickets in this section cannot currently run.",
        "queued": "Tickets in this section are ordered for a future run.",
        "running": "Tickets in this section are currently running.",
        "merged": "Tickets in this section have settled.",
    },
    "7.1 `drain`",
    "Tickets enter intake.",
    "The engine reevaluates their state.",
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
        "retry_pending": "The ticket is waiting for another attempt.",
        "after": "The ticket is ordered after other tickets.",
        "ready": "The ticket is ready for dispatch.",
        "running": "The ticket is running.",
        "merged": "The ticket's change has merged.",
        "already_satisfied": "The ticket settled without a change.",
    },
    "7.1 `drain`",
    "The engine inspects the ticket and its history.",
    "The state can change after intake or a run.",
)
_add(
    "step",
    {
        name: f"Records the {name.replace('_', ' ')} event."
        for name in (
            "requisition_review",
            "implement",
            "check",
            "merge",
            "review",
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
    "The engine begins work.",
    "Inspect the associated record when available.",
)
_add(
    "box",
    {
        "suggestion": "A suggestion proposes work or an idea.",
        "failure_report": "A failure report records a failed dependency or run.",
        "override_report": "An override report records an override.",
        "retro_finding": "A retro finding proposes a follow-up from a retro.",
        "bug_report": "A bug report records a host-reported problem.",
    },
    "9.1 Messages",
    "A message enters the Suggestion Box.",
    "Triage can settle the message.",
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
    "A message enters the Suggestion Box.",
    "Inspect the linked ticket or decision when available.",
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
        "spend": "Summarizes provider costs and token usage.",
    },
    "2.1 Verbs",
    "Select a statistics window.",
    "Inspect the underlying journal for details.",
)
_add(
    "lock",
    {"engine": "The engine lock allows one writer per host.", "commit": "The commit lock serializes git index writes and commits."},
    "10.1 Files",
    "A process requests the lock.",
    "The holder releases the lock when finished.",
)
TOPICS["priority"] = dict(
    what="Priority helps order eligible tickets.", before="A ticket is authored or reordered.", after="The scheduler selects eligible work.", doc="docs/how-clutch-works.md", heading="7.1 `drain`"
)


def topic_text(key):
    entry = TOPICS[key]
    return f"{entry['what']}\nBefore: {entry['before']}\nAfter: {entry['after']}"


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
            text = topic_text(key)
        else:
            text = f"{what}\nBefore: {entry['before']}\nAfter: {entry['after']}"
        result[key] = {"what": what, "before": entry["before"], "after": entry["after"], "text": text, "link": link}
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
