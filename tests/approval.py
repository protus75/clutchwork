"""Record the approval for the ticket content that intake will commit."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Record the approval for the ticket content that intake will commit.
# relates: [clutch/config.py, clutch/journal.py, clutch/tickets.py]
# owner: engine
# verified: d7719818
# hash: b792345f0b51f14ef2383ddf0d253edf5bf93d796ac4e78b98b1053cb196c2d5

import hashlib
from datetime import datetime

from clutch.config import load_config
from clutch.journal import EventType, Journal
from clutch.tickets import TicketInvalid, _intake_claims, validate_ticket


def approve(repo, stem, clock):
    text = (repo / "tickets" / stem / "ticket.md").read_text()
    text, findings = _intake_claims(stem, text, True)
    if findings:
        return
    try:
        validate_ticket(stem, text, repo)
    except TicketInvalid:
        return
    data = text.encode()
    sha = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    journal = Journal(load_config(None, cwd=repo).state_dir, clock)
    events = journal.read()
    last = datetime.fromisoformat(events[-1].ts) if events else clock()
    journal._clock = lambda: max(clock(), last)
    journal.append(EventType.SIGNAL, {"signal": "requisition_verdict", "verdict": "approve", "ticket_sha": sha, "provider": "fixture", "model": "fixture", "spec_version": "1.0"}, ticket=stem)
