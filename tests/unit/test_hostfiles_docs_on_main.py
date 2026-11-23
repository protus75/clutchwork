# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the CORE_TEMPLATE chat-edit rule includes exception (6), which lets documentation-only plan, design, or decision records go straight to main, and that it excludes agent rule files, generated files and frozen documents.
# relates: [clutch/hostfiles.py]
# owner: clutch/hostfiles.py
# verified: 5e7c9aaf
# hash: de2a42997094e60f68a79fad533deb99507a5eb430368791fbb011eac9545150
from clutch.hostfiles import CORE_TEMPLATE


def test_chat_docs_exception_and_exclusions():
    rule = CORE_TEMPLATE.split(b"\n\n", 2)[2].split(b"\n", 1)[0]
    assert (
        b"(6) a new document or documentation-only edit with no matching code change"
        b" that records a plan, design, or decision from this chat, excluding agent"
        b" rule files (CLAUDE.md, AGENTS.md, the core template), generated files,"
        b" and frozen documents" in rule
    )
