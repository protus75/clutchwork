"""Construct an incident-sized, deterministic snapshot host."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Construct an incident-sized, deterministic snapshot host.
# relates: [clutch/box.py, clutch/git.py, clutch/seams.py, tests/integration/test_config.py, tests/integration/test_drain.py]
# owner: engine
# verified: d7719818
# hash: 495527e89de65abb6dbd287bf8508554887c777ffefd996bccf9428227793a51

import json
import subprocess
from pathlib import Path

from clutch.box import Box
from clutch.git import blob_sha
from clutch.seams import LocalFileSystem
from tests.integration.test_config import VALID
from tests.integration.test_drain import confirmed


def git(root, *args, input=None):
    return subprocess.run(["git", "-C", str(root), *args], input=input, text=True, capture_output=True, check=True).stdout.strip()


def build(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "user.email", "fixture@example.com")
    (root / "config.yaml").write_text(VALID)
    (root / "clutch").mkdir()
    (root / "clutch/thing.py").write_text("")
    (root / ".gitignore").write_text(".clutch/\n")
    stems = [f"item-{i:04d}" for i in range(694)]
    for i, stem in enumerate(stems):
        path = root / "tickets" / stem / "ticket.md"
        path.parent.mkdir(parents=True)
        text = confirmed(depends="- item-0693" if 650 <= i < 660 else "none")
        if i >= 680:
            text = text.replace("state: confirmed", "state: draft")
        path.write_text(text)
    git(root, "add", ".")
    git(root, "commit", "-qm", "tickets")
    stream = []
    base = git(root, "rev-parse", "main")
    for i in range(640):
        stream.append(f"commit refs/heads/main\nmark :{i + 1}\ncommitter Fixture <fixture@example.com> 1790000000 +0000\ndata 9\nmerge-{i:03d}\nfrom {base if i == 0 else f':{i}'}\n\n")
    git(root, "fast-import", "--quiet", input="".join(stream))
    git(root, "reset", "-q", "--hard", "main")
    commits = git(root, "log", "--format=%H", "-640", "main").splitlines()
    state = root / ".clutch"
    directory = state / "journal"
    directory.mkdir(parents=True)
    records = []

    def add(stem, body, kind="state_transition"):
        records.append(json.dumps(dict(v=1, type=kind, ts="2026-08-04T12:00:00+00:00", ticket=stem, key=None, body=body), separators=(",", ":")) + "\n")

    for i in range(37120):
        add(stems[i % 640], {"to": "running"})
    for stem, sha in zip(stems[:640], commits):
        add(stem, {"to": "merged", "commit": sha})
    add(stems[640], {"to": "gate_failed", "routed": "reject_queue", "reason": "ticket_changed"})
    sha = blob_sha((root / "tickets" / stems[641] / "ticket.md").read_bytes())
    add(stems[641], {"to": "running", "ticket_sha": sha})
    add(stems[641], {"to": "premise_failed"})
    add(stems[642], {"to": "running"})
    (directory / "000001-20260804.jsonl").write_text("".join(records))
    box = Box(state / "box", LocalFileSystem())
    ids = [box.enqueue(message_class="suggestion", origin="fixture", summary=f"distinct idea {chr(97 + i // 676)}{chr(97 + i // 26 % 26)}{chr(97 + i % 26)}")[0] for i in range(791)]
    return {"events": len(records), "tickets": len(stems), "box": len(box.messages()), "stems": stems, "ids": ids}
