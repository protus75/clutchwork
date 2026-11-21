---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- meta-schema-and-refresh-r2

## Context
- docs/annotations-index-plan.md
- clutch/config.py::Meta
- clutch/config.py::Evidence
- clutch/git.py::Git.merged_tickets
- clutch/git.py::Git.first_parent_squashes
- tests/unit/test_meta_config.py
- tests/unit/test_git_merged_tickets_parse.py
- tests/integration/test_host_contract.py

## Goal / Why
Roadmap row 180, the first slice of rejected `index-build-r1` (its diagnosis names this "Child 1"). After this ticket `Config` accepts an optional `index` block with one key, `embed` (argv list of strings, default unset), and `Git` has a reader returning each first-parent commit's `clutch-ticket` stem, commit sha and changed paths. The index build in `index-build-r2` needs both and the rejected attempt stopped after editing these files untested; shipping them alone keeps that build ticket small.

Decisions this ticket fixes:
- `index.embed` reuses the existing `Argv` type, so an empty list is refused. An omitted `embed` is unset (`None`). `embed: null` is refused by the existing global null rule in `clutch/config.py`, which this ticket does not change. A scalar `embed: "x"` is refused. The plan's `implement_hint` key is not added.
- The reader is a new `Git` method `ticket_touches(dir)` that returns a list of `(stem, commit, paths)` tuples in oldest-first order from `git log --first-parent`. A commit whose `clutch-ticket` trailer is absent, or does not hold exactly one `\S+` value, is omitted. Paths come from the same `git log` call through its name-only output, never a call per commit.

## Boundary contract
### Index config
- disposition: extend
- owner: clutch/config.py
- consumers: `index-build-r2` (`clutch/index.py`), `clutch config` verbs, clutch/docs/host-contract.md
- observable change: optional `index:` block with `embed: [argv]`; omitted `embed` means unset
- compatibility: configs without the block load unchanged; the shipped default is `index: {embed: null}` in the `config-fields` inventory (the model dump, not a config key)
- acceptance: `index` accepts `embed: ["x"]` and an omitted `embed`, refuses `embed: "x"`, `embed: []` and `embed: null`, and a config without the block loads
- tests: tests/unit/test_index_config.py, tests/integration/test_host_contract.py
- post-merge source of truth: clutch/config.py

### Ticket-touch reader
- disposition: extend
- owner: clutch/git.py
- consumers: `index-build-r2` (`clutch/index.py`)
- observable change: new `Git.ticket_touches(dir)` returning `(stem, commit, paths)` per first-parent commit carrying one `clutch-ticket` trailer
- compatibility: existing `Git` methods and their output formats unchanged
- acceptance: canned `git log` output through a fake exec yields the expected tuples, and a commit without a trailer is omitted
- tests: tests/unit/test_git_ticket_touches.py
- post-merge source of truth: clutch/git.py

## Scope in / Scope out
Scope in:
- `clutch/config.py`: add `class Index(StrictModel)` with `embed: Argv | None = None`, and `index: Index = Index()` on `Config`.
- `clutch/docs/host-contract.md`: in the `config-fields` block add `index: {embed: null}` to `Config` defaults (after `meta`) and an `Index` model row with `required: []` and `defaults: {embed: unset}`, matching how `Evidence` and `notify` rows read. Edit nothing else there. `tests/integration/test_host_contract.py` already compares this block to `clutch/config.py` model for model, so it is run and not edited.
- `clutch/git.py`: add `Git.ticket_touches`, reusing `_run` and the `merged_tickets` trailer parse.
- New `tests/unit/test_index_config.py` and `tests/unit/test_git_ticket_touches.py`; the latter uses a fake exec like `tests/unit/test_git_merged_tickets_parse.py` (copied, not edited).

Scope out: no `clutch/index.py`, merge hook, `index` verb, or docs for a verb (`index-build-r2` and later rows 181-182 own them); no `implement_hint`; no change to the null rule or `first_parent_squashes`.

## Scope fence
- clutch/config.py
- clutch/git.py
- clutch/docs/host-contract.md
- tests/unit/test_index_config.py
- tests/unit/test_git_ticket_touches.py

## Acceptance criteria
1. `tests/unit/test_index_config.py` asserts `Config.model_fields["index"].default == Index()`, `Index().embed is None`, `Index(embed=["x"]).embed == ["x"]`, and that `Index(embed="x")` and `Index(embed=[])` raise `ValidationError`; accepting a string or empty list fails it. Check: `./dev.py test tests/unit/test_index_config.py`.
2. `tests/unit/test_index_config.py` loads a config through the loader with `index: {embed: null}` and asserts `ConfigError` whose message contains `null`, and loads one without an `index` block and asserts `cfg.index.embed is None`; a loader that accepts the null fails it. Check: `./dev.py test tests/unit/test_index_config.py`.
3. `tests/integration/test_host_contract.py::test_host_contract_schema_coverage` passes with the `Index` row and `index: {embed: null}` default in `clutch/docs/host-contract.md`; a missing row or a wrong default fails it. Check: `./dev.py test tests/integration/test_host_contract.py`.
4. `tests/unit/test_git_ticket_touches.py` feeds canned `git log` output through a fake exec and asserts `ticket_touches` returns `[("a", "aaa", ["x.py", "y/z.md"]), ...]` with stem, commit and paths, that the argv contains `--first-parent`, and that a commit without a `clutch-ticket` trailer and one with two trailer values are omitted; returning every commit, or an empty paths list for a commit that changed files, fails it. Check: `./dev.py test tests/unit/test_git_ticket_touches.py`.
5. `tests/unit/test_git_ticket_touches.py` asserts the fake exec is called once for any number of commits, not once per commit; a per-commit call fails it. Check: `./dev.py test tests/unit/test_git_ticket_touches.py`.

## Verification
```
./dev.py test tests/unit/test_index_config.py tests/unit/test_git_ticket_touches.py tests/integration/test_host_contract.py tests/unit/test_git_merged_tickets_parse.py
```

## Definition of rejected
The branch is thrown away if it touches `clutch/index.py`, `clutch/merge.py`, `clutch/mergequeue.py` or `clutch/__main__.py`, adds a key other than `embed` to `index`, relaxes the null rule, or changes the output of an existing `Git` method.

## Time budget
- expected: 12m
- stuck: 24m
