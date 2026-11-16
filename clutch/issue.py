"""Build a person-reviewed upstream issue link."""

import platform
from collections.abc import Callable
from importlib.metadata import version
from urllib.parse import urlencode

from clutch import observe, runner

CLASSES = ("state-loss", "secret-leak", "bad-merge", "engine-stuck", "wrong-refusal")
MAX_LINK_BYTES = 3000


def link(issue_class: str | None, title: str, body: str, scrub: Callable[[str], str]) -> str:
    if issue_class not in CLASSES:
        raise runner.Refusal(f"--class must be one of: {', '.join(CLASSES)}", "only critical bugs are filed upstream; name a non-critical clutch problem to the user in chat instead")
    if not body.strip():
        raise runner.Refusal("--body file is empty", "write the clutch file, the defect, and minimal evidence into the --body file")
    title = f"[critical:{issue_class}] {title}"
    body = body.rstrip() + "\n\n---\nclutchwork " + version("clutchwork") + ", Python " + platform.python_version() + ", " + platform.system() + "\nFiled with clutch issue"
    url = observe.repository_url() + "/issues/new?" + urlencode({"title": scrub(title), "body": scrub(body)})
    if len(url) > MAX_LINK_BYTES:
        raise runner.Refusal(f"link is {len(url)} bytes, over the 3000-byte limit", "shorten the body; quote only the lines that show the defect")
    return url
