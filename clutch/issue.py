"""Build a person-reviewed upstream issue link."""

import platform
from collections.abc import Callable
from importlib.metadata import version
from urllib.parse import urlencode

from clutch import observe, runner

CRITICAL = ("state-loss", "secret-leak", "bad-merge", "engine-stuck", "wrong-refusal")
CLASSES = CRITICAL + ("process-gap",)
MAX_LINK_BYTES = 3000


def link(issue_class: str | None, title: str, body: str, scrub: Callable[[str], str]) -> str:
    if issue_class not in CLASSES:
        raise runner.Refusal(
            f"--class must be one of: {', '.join(CLASSES)}",
            "only a critical bug, or a process gap that cost a real run an attempt or review cycle, is filed upstream; name anything else to the user in chat instead",
        )
    if not body.strip():
        raise runner.Refusal("--body file is empty", "write the clutch file, the defect, and minimal evidence into the --body file")
    title = f"[critical:{issue_class}] {title}" if issue_class in CRITICAL else f"[process-gap] {title}"
    body = body.rstrip() + "\n\n---\nclutchwork " + version("clutchwork") + ", Python " + platform.python_version() + ", " + platform.system() + "\nFiled with clutch box issue"
    url = observe.repository_url() + "/issues/new?" + urlencode({"title": scrub(title), "body": scrub(body)})
    if len(url) > MAX_LINK_BYTES:
        raise runner.Refusal(f"link is {len(url)} bytes, over the 3000-byte limit", "shorten the body; quote only the lines that show the defect")
    return url
