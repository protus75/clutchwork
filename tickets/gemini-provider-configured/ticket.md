---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- gemini-provider

## Context
- config.yaml
- clutch/docs/host-gemini.md
- clutch/providers.py::ProviderLLM.preflight
- tickets/gemini-provider/ticket.md#Scope in / Scope out

## Goal / Why
After this ticket this repo's `config.yaml` declares the `gemini` provider (`kind: cli`, `package: "@google/gemini-cli"`, `auth: GEMINI_API_KEY`), using the declaration in `clutch/docs/host-gemini.md`.

Why: `gemini-provider` merged the adapter but left the declaration as "an operator edit after setup" (its Scope in / Scope out). Roadmap decision 19 has no operator, so the edit never happened. `ProviderLLM.preflight` compares only declared providers with their latest release, so no notice ever reported the project's `gemini` (0.68.0 in `node_modules/.bin`, latest 0.70.0) as stale. Meanwhile an image-generation decision rested on A0 fact 7, captured with a separate 0.49.0 global install. Declaring it puts gemini under the existing stale-CLI notice. Declaring without routing costs nothing at preflight, because probes run only for routed candidates.

## Boundary contract
none
- reason: configuration only; the instance config gains one provider entry that the existing loader schema already accepts, and no code, format or consumer contract changes

## Scope in / Scope out
Scope in:
- `config.yaml`: add one `providers` entry for `gemini` after `codex`, copied from the gemini setup guide's declaration (`name`, `kind`, `package`, `auth`, `models_by_tier`, `limits`). Update the header comment, which says both providers use ambient CLI login with no `auth`, so it names gemini's `GEMINI_API_KEY` key.
- Nothing else in `config.yaml` changes. No `routing` row names gemini.

Scope out:
- Routing gemini to any surface, and upgrading the installed CLI. The upgrade is the stale-CLI notice's own paved road (`clutch provider install gemini`).
- The authoring cause (a ticket deferring required work to an operator): `operator-deferral-snag`.

## Scope fence
- config.yaml

## Acceptance criteria
1. The `uv run python -c` command in `## Verification` exits 0. It loads `config.yaml` through `clutch.config.load_config_text` and asserts that a provider named `gemini` has `kind == "cli"`, `package == "@google/gemini-cli"` and `auth == "GEMINI_API_KEY"`, and that no routing candidate names `gemini`. It fails on the current `config.yaml`, which has no gemini provider.

## Verification
```
uv run python -c "import pathlib; from clutch.config import load_config_text; p = pathlib.Path('config.yaml').resolve(); c = load_config_text(p.read_text(), path=p, cwd=p.parent); g = [x for x in c.providers if x.name == 'gemini']; assert len(g) == 1 and g[0].kind == 'cli' and g[0].package == '@google/gemini-cli' and g[0].auth == 'GEMINI_API_KEY', g; assert not [k for r in c.routing for k in r.candidates if k.provider == 'gemini']"
```

## Definition of rejected
- a `routing` row names gemini, or any file other than `config.yaml` changes;
- the claude or codex provider entries change.

## Time budget
- expected: 5m
- stuck: 10m
