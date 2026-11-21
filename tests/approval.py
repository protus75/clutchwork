"""Record the approval for the ticket content that intake will commit."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Record the approval for the ticket content that intake will commit.
# relates: [clutch/config.py, clutch/journal.py, clutch/tickets.py]
# owner: engine
# verified: 9c24a9bd
# hash: 3ee55cba32fce246c602f60b4aafa330079f39dbf6ccb184e92f3ce5e3424aef

import asyncio
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from clutch.caps import capability
from clutch.config import load_config
from clutch.git import Git
from clutch.journal import EventType, Journal
from clutch.lockfile import CommitLock
from clutch.requisition import review_input_identity
from clutch.runner import SPECS_DIR
from clutch.seams import SubprocessExec
from clutch.tickets import TicketInvalid, _intake_claims, validate_ticket


def approve(repo, stem, clock):
    text = (repo / "tickets" / stem / "ticket.md").read_text()
    text, findings = _intake_claims(stem, text, True)
    if findings:
        return
    try:
        ticket = validate_ticket(stem, text, repo)
    except TicketInvalid:
        return
    data = text.encode()
    sha = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    config = load_config(None, cwd=repo)
    journal = Journal(config.state_dir, clock)
    events = journal.read()
    last = datetime.fromisoformat(events[-1].ts) if events else clock()
    journal._clock = lambda: max(clock(), last)
    git = Git(SubprocessExec(), env=os.environ, timeout=30, commit_lock=CommitLock(config.state_dir, clock=clock, sleep=asyncio.sleep))

    async def gather():
        coverage = config.state_dir / "coverage-map.json" if config.review.coverage_map is not None else None
        return await review_input_identity(repo, text, ticket, config, git, SPECS_DIR, coverage, events, tier=capability(ticket, events)[0])

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        identity = asyncio.run(gather())
    else:
        with ThreadPoolExecutor(max_workers=1) as pool:
            identity = pool.submit(lambda: asyncio.run(gather())).result()
    journal.append(
        EventType.SIGNAL,
        {"signal": "requisition_verdict", "verdict": "approve", "ticket_sha": sha, "provider": "fixture", "model": "fixture", "spec_version": "1.0", "input_identity": identity},
        ticket=stem,
    )
