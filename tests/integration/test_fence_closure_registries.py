# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test fence closure registries
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 595b9e84
# hash: a3029d8007fc77553d07984672a791fb80b6dca57aed822ff11cf3252dc5f8ea
from pathlib import Path

from clutch.specs import load_spec, render

ROOT = Path(__file__).resolve().parents[2]

# Each phrase rules out omitting that part of the registry rule or its existing guard.
PHRASES = (
    "an entry of an in-code registry, table, mapping, or closed vocabulary",
    "grep `tests/` for the collection's name",
    "compares that collection or a filtered subset of it for exact equality or lists it in full",
    "every file holding a table that a test requires to match the collection entry for entry",
    "A test that only imports or iterates the collection, or reads one entry the change leaves alone, is not a hit.",
    "adds, removes, renames, or moves a member of a set",
    "asserts against the changed set or hardcodes the moved path",
    "A mere textual mention, a path built under `tmp_path`, or a historical form the ticket keeps valid is not a hit.",
)


def test_authoring_guide_traces_in_code_collections():
    guide = " ".join((ROOT / "clutch/docs/host-authoring.md").read_text().split())
    for phrase in PHRASES:
        assert phrase in guide
