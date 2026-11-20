# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test visual fixtures
# relates: [clutch/config.py, clutch/policy.py, eval/visual_harness.py]
# owner: engine
# verified: 96e46658
# hash: 5fc756bf6cee8a1995b9a2885e54c0db5bd8e1f83631f4e611352e324d7b15ce
import json
from collections import Counter

import pytest

from clutch.config import load_config
from clutch.policy import visual_identity
from eval.visual_harness import CASES, ROOT, load_cases


def test_committed_visual_fixtures():
    judge = visual_identity(load_config(None, cwd=ROOT))["review_visual"]["rows"]["medium"]["provider"]
    cases = load_cases(CASES, judge)
    all_cases = load_cases(CASES, judge, labelled_only=False)
    assert 20 <= len(cases) <= 24
    assert len(cases) == len(all_cases)
    panels = {(case.data.panel.provider, case.data.panel.model) for case in cases}
    assert len(panels) == 1
    provider, model = next(iter(panels))
    assert provider and model and provider != judge
    with pytest.raises(ValueError, match="panel provider"):
        load_cases(CASES, provider)
    verdicts = Counter(case.data.label.verdict for case in cases)
    assert verdicts["accept"] >= 5
    assert verdicts["reject"] >= 5
    generated = [case for case in cases if case.data.mode == "generate"]
    assert len(generated) >= 6
    for case in generated:
        assert {"identity", "placement", "lighting", "unchanged", "artifacts"} <= set(case.data.label.rows)

    report = json.loads((ROOT / "eval" / "visual_report.json").read_text())
    assert set(report) == {"case_count", "overall", "rows", "verdict"}
    assert report["verdict"] in {"GO", "NO_GO"}
    assert report["case_count"] >= 20
    assert 0 <= report["overall"] <= 1
    assert set(report["rows"]) <= {row for case in cases for row in case.data.label.rows}
