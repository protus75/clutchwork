# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test requisition sibling tickets
# relates: [clutch/requisition.py, clutch/tickets.py]
# owner: engine
# verified: 9a610809
# hash: 7bf05a24ead784d78012a580244ed75bd77b4a21de4693a446aa584f771934f3
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


def test_review_renders_siblings_and_skips_bad_ticket(monkeypatch):
    own, other = ticket("own"), ticket("other")
    monkeypatch.setattr(requisition, "review_target", lambda *args: own)
    monkeypatch.setattr(requisition, "_base_render", lambda *args: "base")
    monkeypatch.setattr(requisition, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(version="1.0", effort="high")))
    captured = []
    monkeypatch.setattr(requisition, "render", lambda spec, values: captured.append(values.copy()) or "prompt")

    def parse(stem, text, repo):
        if text == "broken":
            raise TicketInvalid([])
        return other

    monkeypatch.setattr(requisition, "parse_ticket", parse)

    async def call(*args, **kwargs):
        return dict(text=json.dumps(dict(verdict="approve", summary="reviewed", findings=[])), input_tokens=1, output_tokens=1, provider="fake", model="m", usd=0.0)

    async def race(fn, timeout):
        return await fn()

    monkeypatch.setattr(requisition, "llm_call", call)
    driver = SimpleNamespace(
        journal=SimpleNamespace(read=lambda: []), retry_cap=0, spool=SimpleNamespace(write=lambda *args: None), _active=True, race=race, effects=None, watched_llm=lambda: None, redactor=None
    )
    for files in ({"tickets/other/ticket.md": "valid", "tickets/bad/ticket.md": "broken"}, {}):
        asyncio.run(
            requisition.review_ticket(
                driver,
                repo=MemoryPath(files=files),
                stem="own",
                text="ticket",
                specs_dir=MemoryPath(),
                coverage_map=None,
                tier="high",
                stem_slot="s",
                run_seq=1,
                attempt=1,
                call_seq=1,
                expected_budget="surface",
                prior="none",
            )
        )
    assert "other" in captured[0]["sibling_tickets"]
    assert captured[1]["sibling_tickets"] == "none"
