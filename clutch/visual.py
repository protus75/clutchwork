"""Visual judge reply validation and strict-majority aggregation."""

from collections import Counter
from typing import Literal

from pydantic import ValidationError

from clutch.artifacts import FrozenModel, NonBlank


class Row(FrozenModel):
    id: NonBlank
    verdict: Literal["pass", "fail", "unsure"]
    observation: NonBlank


class Reply(FrozenModel):
    rows: list[Row]
    verdict: Literal["accept", "reject", "unsure"]
    reason: NonBlank


def rubric_ids(visual_criteria: list[str], mode: str) -> list[str]:
    return [*visual_criteria, *(["identity", "placement", "lighting", "unchanged", "artifacts"] if mode == "generate" else [])]


def parse_reply(text: str, row_ids: list[str]) -> Reply:
    try:
        reply = Reply.model_validate_json(text)
    except ValidationError as exc:
        raise ValueError(f"invalid visual reply: {exc}; return the specified JSON schema") from exc
    ids = [row.id for row in reply.rows]
    if len(ids) != len(set(ids)):
        raise ValueError("repeated rubric row; return each rubric id exactly once")
    missing, extra = set(row_ids) - set(ids), set(ids) - set(row_ids)
    if missing or extra:
        raise ValueError(f"rubric rows missing {sorted(missing)} or unknown {sorted(extra)}; return exactly the supplied rubric ids")
    return reply


def _winner(values: list[str]) -> str:
    verdict, count = Counter(values).most_common(1)[0]
    return verdict if count > len(values) / 2 else "unsure"


def majority(replies: list[Reply]) -> Reply:
    if not replies:
        raise ValueError("no replies; provide at least one valid reply")
    if len(replies) == 1:
        return replies[0]
    ids = [row.id for row in replies[0].rows]
    if any({row.id for row in reply.rows} != set(ids) or len(reply.rows) != len(ids) for reply in replies):
        raise ValueError("replies have different rubric rows; provide replies validated against the same rubric")
    rows = []
    for row_id in ids:
        samples = [next(row for row in reply.rows if row.id == row_id) for reply in replies]
        verdict = _winner([row.verdict for row in samples])
        observation = next((row.observation for row in samples if row.verdict == verdict), "No strict majority among observations.")
        rows.append(Row(id=row_id, verdict=verdict, observation=observation))
    verdict = _winner([reply.verdict for reply in replies])
    reason = next((reply.reason for reply in replies if reply.verdict == verdict), "No strict majority among verdicts.")
    return Reply(rows=rows, verdict=verdict, reason=reason)


def rank(candidates: list[tuple[int, str, int, float | None, int | None]]) -> list[tuple[int, str, int, float | None, int | None]]:
    """Order candidates by verdict, passing rows, preservation and presence."""
    order = {"accept": 2, "unsure": 1, "reject": 0}
    return sorted(candidates, key=lambda c: (order[c[1]], c[2], c[3] if c[3] is not None else -1, c[4] if c[4] is not None else -1), reverse=True)


def decide(candidates: list[tuple[int, str, int, float | None, int | None]]) -> tuple[int | None, str | None]:
    ordered = rank(candidates)
    if not ordered or any(c[1] == "unsure" for c in ordered) or ordered[0][1] != "accept":
        return None, "visual_undecided"
    if len(ordered) > 1 and ordered[0][2] <= ordered[1][2]:
        return None, "visual_undecided"
    return ordered[0][0], None
