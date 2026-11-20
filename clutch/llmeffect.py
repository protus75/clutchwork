"""The LLM call as an effect.

Keyed `llm/<stem>/<run_seq>/<surface>/<attempt>/<call_seq>`: one cost-bearing completion per call,
and a same-key re-entry (no intervening terminal, so the same run_seq) replays the recorded result
instead of calling. The driver reaches the model only through `llm_call`.
"""

import re
from dataclasses import asdict, replace
from typing import Any

from clutch.effects import Effects
from clutch.llm import LLM, LLMRequest
from clutch.redact import Redactor


def scoped_seq(scope: str | None, n: int) -> int | str:
    if scope is None:
        return n
    if re.fullmatch(r"[a-z][a-z0-9]*", scope) is None:
        raise ValueError("invalid key scope")
    return f"{scope}-{n}"


def llm_key(stem: str, run_seq: int | str, surface: str, attempt: int, call_seq: int) -> str:
    return "/".join(("llm", stem, str(run_seq), surface, str(attempt), str(call_seq)))


def member_index(call_key: str | None) -> int | None:
    if not isinstance(call_key, str):
        return None
    parts = call_key.split("/")
    if len(parts) != 6 or parts[0] != "llm" or not all(parts[1:]):
        return None
    match = re.fullmatch(r"m([0-9]+)-[0-9]+", parts[2])
    if match is None or not parts[4].isdigit() or not parts[5].isdigit():
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _cost(result: dict[str, Any]) -> dict[str, Any]:
    return {k: result[k] for k in ("usd", "input_tokens", "output_tokens", "provider", "model")}


async def llm_call(effects: Effects, llm: LLM, req: LLMRequest, redactor: Redactor, *, ticket: str | None, stem: str, run_seq: int | str, attempt: int, call_seq: int) -> dict[str, Any]:
    key = llm_key(stem, run_seq, req.surface, attempt, call_seq)

    async def record(operation):
        async def action():
            result = await operation()
            return asdict(replace(result, text=redactor.scrub(result.text)))

        return await effects.run(action, key=key, ticket=ticket, cost=_cost)

    # A replay has no admission, wait, meter, outcome or cooldown side effect.
    if key in effects._completed or not hasattr(llm, "admitted_call"):
        return await record(lambda: llm.call(req))
    return await llm.admitted_call(req, ticket=ticket, call_key=key, effect=record)
