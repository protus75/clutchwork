"""The host guide provides a discoverable path to the first merge."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: The host guide provides a discoverable path to the first merge.
# relates: []
# owner: engine
# verified: 148a8874
# hash: d11a40f2cd31bcafa11e7cbf5a880cd4b9a6e39b3dd76015f47948a0bfaab4bb

import re
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "clutch/docs/host-contract.md"


def test_onboarding_and_operating_sections():
    doc = DOC.read_text()
    headings = ("Onboarding a host", "Operating facts")
    sections = {}
    for heading in headings:
        matches = list(re.finditer(rf"^## {heading}$", doc, re.M))
        assert len(matches) == 1, heading
        assert matches[0].start() < doc.index("## Complete field inventory")
        start = matches[0].end()
        end = re.search(r"^## ", doc[start:], re.M)
        sections[heading] = doc[start : start + end.start() if end else None]

    onboarding = sections[headings[0]]
    assert len(re.findall(r"^\d+\. ", onboarding, re.M)) >= 8
    verbs = ("clutch provider install", "clutch config init", "clutch host doctor", "clutch provider probe", "clutch host core", "clutch ticket new", "clutch ticket lint", "clutch ticket review")
    positions = [onboarding.index(verb) for verb in verbs]
    assert positions == sorted(positions)
    assert re.search(r"clutch engine (?:drain|serve)", onboarding[positions[-1] :])

    operating = sections[headings[1]]
    for term in ("clutch.lock", "commit.lock", "state_dir", "uv sync", "upgrade", "rollback"):
        assert term in operating, term
    for section in sections.values():
        for forbidden in ("shell=True", "./dev.py", "```"):
            assert forbidden not in section, forbidden
