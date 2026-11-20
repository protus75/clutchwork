import pytest
from pydantic import ValidationError

from clutch.artifacts import DiagnosisReply, Finding, ReviewVerdict
from clutch.panel import DIAGNOSIS_ORDER, TRIAGE_ORDER, Candidate, DroppedMember, PanelFacts, PanelMember, best_of_n, findings_union, majority_verdict
from clutch.triage import TriageReply


def member(verdict, provider="p", model="m"):
    return PanelMember(provider=provider, model=model, verdict=verdict)


def finding(message, line=None, code="logic", road="first"):
    return Finding(code=code, path="a", line=line, message=message, paved_road=road)


def review(verdict, summary, findings=()):
    return ReviewVerdict(verdict=verdict, summary=summary, findings=list(findings))


def test_union_verdict_messages_and_agreement():
    replies = [review("snag", "one", [finding("a", 1), finding("other", 2)]), review("snag", "two", [finding("b", 1, road="second"), finding("a", 1), finding("no line")])]
    result, facts = findings_union(replies, [member("snag"), member("snag")])
    assert result.verdict == "snag"
    assert result.summary == "one\ntwo"
    assert [(f.line, f.message, f.paved_road) for f in result.findings] == [(1, "a\nb\nno line", "first"), (2, "other", "first")]
    assert [(f.agreement, f.members) for f in facts.merged] == [("2/2", [0, 1]), ("1/2", [0])]
    result, _ = findings_union([review("approve", "yes"), replies[0]], [member("approve"), member("snag")])
    assert result.verdict == "snag"
    result, facts = findings_union([replies[0], review("rma", "ticket", [finding("fix ticket", code="ticket")])], [member("snag"), member("rma")])
    assert result.verdict == "rma"
    assert [f.code for f in result.findings] == ["ticket"]
    assert [f.finding.code for f in facts.merged] == ["logic", "logic", "ticket"]


def test_line_after_lineless_joins_group():
    result, _ = findings_union([review("snag", "one", [finding("a")]), review("snag", "two", [finding("b", 3)])], [member("snag"), member("snag")])
    assert [(f.line, f.message) for f in result.findings] == [(None, "a\nb")]


def test_majority_and_ties():
    replies = [DiagnosisReply(verdict=v, lessons=[str(i)]) for i, v in enumerate(("retry", "escalate", "escalate"))]
    result, facts = majority_verdict(replies, DIAGNOSIS_ORDER, [member(r.verdict) for r in replies], [DroppedMember(index=3, failure_class="timeout")])
    assert result is replies[1]
    assert facts.verdict_counts == {"retry": 1, "escalate": 2}
    assert facts.member_count == 4 and facts.dropped[0].failure_class == "timeout"
    assert facts.agreement_kind == "samples"
    assert majority_verdict(replies[:2], DIAGNOSIS_ORDER, [member("retry"), member("escalate", model="other")])[0] is replies[1]
    assert majority_verdict(replies[:2], DIAGNOSIS_ORDER, [member("retry"), member("escalate", model="other")])[1].agreement_kind == "models"
    with pytest.raises(ValueError):
        majority_verdict(replies[:2], ("retry",), [member("retry"), member("escalate")])
    triage = [TriageReply(verdict=v, link=None, summary="s", rationale="r", evidence=[], reopen_after_days=None if v == "author" else 1) for v in ("author", "declined")]
    assert majority_verdict(triage, TRIAGE_ORDER, [member(r.verdict) for r in triage])[0] is triage[1]


def test_best_selection_and_retirement():
    candidates = [Candidate(check_passed=p, soft_findings=s, inserted_lines=lines) for p, s, lines in [(False, 0, 0), (True, 2, 1), (True, 1, 8), (True, 1, 4), (True, 1, 4)]]
    kept, retired, facts = best_of_n(candidates, [member("done")] * 5)
    assert kept == 3 and retired == [0, 1, 2, 4] and facts.kept_index == 3
    kept, retired, _ = best_of_n(candidates[:1], [member("done")])
    assert kept is None and retired == [0]


def test_facts_closed_shape():
    values = dict(combiner="wrong", member_count=1, members=[member("retry")], verdict_counts={"retry": 1}, agreement_kind="samples")
    with pytest.raises(ValidationError):
        PanelFacts(**values)
    values["combiner"] = "majority-verdict"
    with pytest.raises(ValidationError):
        PanelFacts(**values, extra=1)
