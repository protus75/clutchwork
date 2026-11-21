# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify requisition review has one LLM call site.
# relates: []
# owner: engine
# verified: 5110a5cc
# hash: c32dcf0fcc69832c17d68b442dfafc24e99507f50143ad1830545b569c39814b
import ast
from pathlib import Path


def test_one_llm_call_site_inside_review_ticket():
    source = (Path(__file__).resolve().parents[2] / "clutch/requisition.py").read_text()
    tree = ast.parse(source)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "llm_call"]
    review = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "review_ticket")
    assert len(calls) == 1 and calls[0] in list(ast.walk(review))
