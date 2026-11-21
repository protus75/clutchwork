# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify rework uses the review sequence scanner.
# relates: []
# owner: engine
# verified: 5110a5cc
# hash: 962bdc8b8c463356109469b40c89dba3e3c7c43673d6dede26b946747ccef091
import ast
from pathlib import Path


def test_rework_calls_sequence_scanner_once():
    source = (Path(__file__).resolve().parents[2] / "clutch/rework.py").read_text()
    tree = ast.parse(source)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "next_review_seq"]
    assert len(calls) == 1
    assert "llm/{ticket.stem}/{key_attempt}/requisition_review/{attempt}/" not in source
