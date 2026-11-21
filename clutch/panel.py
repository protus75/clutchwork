"""Pure selection and aggregation of independent panel replies."""

from collections import Counter
from typing import Literal, Protocol, Sequence, TypeVar

from pydantic import Field

from clutch.artifacts import Finding, FrozenModel, NonBlank, ReviewVerdict

DIAGNOSIS_ORDER = ("escalate", "abandon-human", "split", "reject", "retry")
TRIAGE_ORDER = ("declined", "tombstone", "author")


class PanelMember(FrozenModel):
    provider: NonBlank
    model: NonBlank
    verdict: NonBlank


class DroppedMember(FrozenModel):
    index: int
    failure_class: NonBlank


class MergedFinding(FrozenModel):
    finding: Finding
    agreement: NonBlank
    members: list[int]


class PanelFacts(FrozenModel):
    combiner: Literal["findings-union", "majority-verdict", "best-of-n"]
    member_count: int
    members: list[PanelMember]
    verdict_counts: dict[str, int]
    dropped: list[DroppedMember] = Field(default_factory=list)
    merged: list[MergedFinding] = Field(default_factory=list)
    kept_index: int | None = None
    agreement_kind: Literal["samples", "models"]


def _facts(combiner, members, dropped, *, merged=None, kept_index=None):
    return PanelFacts(
        combiner=combiner,
        member_count=len(members) + len(dropped),
        members=members,
        verdict_counts=dict(Counter(member.verdict for member in members)),
        dropped=dropped,
        merged=merged or [],
        kept_index=kept_index,
        agreement_kind="samples" if len({(m.provider, m.model) for m in members}) == 1 else "models",
    )


def findings_union(replies: Sequence[ReviewVerdict], members: list[PanelMember], dropped: list[DroppedMember] | None = None, *, rma_code: str | None = "ticket") -> tuple[ReviewVerdict, PanelFacts]:
    """Merge findings in reply order; member indexes refer to the supplied replies."""
    if not replies or len(replies) != len(members):
        raise ValueError("one member is required for each nonempty reply")
    groups: list[tuple[Finding, list[str], list[int]]] = []
    for index, reply in enumerate(replies):
        for finding in reply.findings:
            matching = [(i, f) for i, (f, _, _) in enumerate(groups) if (f.code, f.path) == (finding.code, finding.path)]
            exact = next((i for i, f in matching if f.line == finding.line), None)
            if finding.line is None:
                target = matching[0][0] if matching else None
            else:
                target = exact if exact is not None else next((i for i, f in matching if f.line is None), None)
            if target is None:
                groups.append((finding, [finding.message], [index]))
            else:
                _, messages, indexes = groups[target]
                if finding.message not in messages:
                    messages.append(finding.message)
                if index not in indexes:
                    indexes.append(index)
    merged = [MergedFinding(finding=f.model_copy(update={"message": "\n".join(messages)}), agreement=f"{len(indexes)}/{len(replies)}", members=indexes) for f, messages, indexes in groups]
    verdict = max((reply.verdict for reply in replies), key={"approve": 0, "snag": 1, "rma": 2}.get)
    findings = [item.finding for item in merged if verdict != "rma" or rma_code is None or item.finding.code == rma_code]
    combined = type(replies[0])(verdict=verdict, summary="\n".join(reply.summary for reply in replies), findings=findings)
    return combined, _facts("findings-union", members, dropped or [], merged=merged)


class _Verdict(Protocol):
    verdict: str


Reply = TypeVar("Reply", bound=_Verdict)


def majority_verdict(replies: Sequence[Reply], safer_first: Sequence[str], members: list[PanelMember], dropped: list[DroppedMember] | None = None) -> tuple[Reply, PanelFacts]:
    if not replies or len(replies) != len(members):
        raise ValueError("one member is required for each nonempty reply")
    counts = Counter(reply.verdict for reply in replies)
    tied = {verdict for verdict, count in counts.items() if count == max(counts.values())}
    if len(tied) > 1:
        if not tied <= set(safer_first):
            raise ValueError("every tied verdict must occur in the safer-first order")
        winner = min(tied, key=safer_first.index)
    else:
        winner = next(iter(tied))
    return next(reply for reply in replies if reply.verdict == winner), _facts("majority-verdict", members, dropped or [])


class Candidate(FrozenModel):
    check_passed: bool
    soft_findings: int
    inserted_lines: int


def best_of_n(candidates: Sequence[Candidate], members: list[PanelMember], dropped: list[DroppedMember] | None = None) -> tuple[int | None, list[int], PanelFacts]:
    if len(candidates) != len(members):
        raise ValueError("one member is required for each candidate")
    passing = (i for i, candidate in enumerate(candidates) if candidate.check_passed)
    kept = min(passing, key=lambda i: (candidates[i].soft_findings, candidates[i].inserted_lines, i), default=None)
    return kept, [i for i in range(len(candidates)) if i != kept], _facts("best-of-n", members, dropped or [], kept_index=kept)
