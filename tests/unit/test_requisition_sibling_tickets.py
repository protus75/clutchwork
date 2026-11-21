# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test requisition sibling tickets
# relates: [clutch/requisition.py, clutch/tickets.py]
# owner: engine
# verified: 595b9e84
# hash: 9b312845761047b431864121d386fcfc9a531c620a09ca0cc140e10665da8bb8
import asyncio
import json
from types import SimpleNamespace

from clutch import requisition
from clutch.tickets import TicketInvalid


def ticket(stem, fence=("src/a.py",), state="confirmed", depends=(), scope="Scope in: change the interface.", **sections):
    return SimpleNamespace(stem=stem, scope_fence=fence, frontmatter=SimpleNamespace(state=state), depends=depends, sections={"Scope in / Scope out": scope, **sections})


def test_qualifying_sibling_and_excluded_sections():
    sibling = ticket("sibling", scope="Scope in: special interface", **{"Acceptance criteria": "secret criterion", "Verification": "secret verification"})
    block = requisition.sibling_tickets_block(ticket("own"), [sibling], set())
    assert "sibling" in block and "src/a.py" in block and "special interface" in block
    assert "secret criterion" not in block and "secret verification" not in block


def test_exclusions():
    own = ticket("own", depends=("dependency",))
    siblings = [ticket("draft", state="draft"), ticket("settled"), ticket("unrelated", fence=("src/b.py",)), ticket("dependency"), ticket("dependent", depends=("own",)), own]
    for sibling in siblings:
        assert requisition.sibling_tickets_block(own, [sibling], {"settled"}) == "none"


def test_rank_cap_and_truncation():
    own = ticket("own", fence=("src/a", "src/b", "src/c"))
    siblings = [
        ticket(name, fence=fence, scope="X" * 4000)
        for name, fence in [
            ("g", ("src/a",)),
            ("f", ("src/a",)),
            ("e", ("src/a",)),
            ("d", ("src/a", "src/b")),
            ("c", ("src/a", "src/b")),
            ("b", ("src/a", "src/b", "src/c")),
            ("a", ("src/a", "src/b")),
        ]
    ]
    block = requisition.sibling_tickets_block(own, siblings, set())
    assert [part.splitlines()[0] for part in block.split("\n\n")] == ["b", "a", "c", "d", "e"]
    assert "X" * 1500 in block and "X" * 1501 not in block


class MemoryPath:
    def __init__(self, name="", files=None):
        self.name = name
        self.files = files if files is not None else {}

    def __truediv__(self, part):
        return MemoryPath(f"{self.name}/{part}".strip("/"), self.files)

    @property
    def parent(self):
        return MemoryPath(self.name.rsplit("/", 1)[0], self.files)

    def glob(self, pattern):
        return [MemoryPath(name, self.files) for name in self.files if name.startswith("tickets/") and name.endswith("/ticket.md")]

    def read_text(self):
        return self.files.get(self.name, "spec")
