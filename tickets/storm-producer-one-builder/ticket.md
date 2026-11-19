---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- projection-helpers-single-owner

## Context
- clutch/daemon.py::storm_producer
- clutch/box.py::BOX_DIR
- tests/integration/test_projection_helpers_source.py

## Goal / Why
Roadmap section 2.1 item 10, left out of row 125. Today `storm_producer(root=<config>.state_dir / BOX_DIR, fs=..., journal=..., clock=...)` is built by hand at 15 production sites: `clutch/__main__.py` (1), `clutch/driver.py` (1), `clutch/retro.py` (3), `clutch/runner.py` (4), `clutch/stages.py` (4), `clutch/triage.py` (1). Each site repeats the box-directory rule. After this ticket, `clutch/daemon.py` has one builder, `storm_producer_for_config(config, *, fs, journal, clock)`, that owns the `config.state_dir / BOX_DIR` argument and delegates to `storm_producer`. Every production site calls the builder, and a source scan fails if a site calls `storm_producer` directly. A change to where the box lives or how it is composed then happens in one place.

## Boundary contract
### Storm-producer composition
- disposition: extend
- owner: clutch/daemon.py
- consumers: `__main__.py`, `driver.py`, `retro.py`, `runner.py`, `stages.py` and `triage.py`, which build the box
- observable change: none at runtime. The same Box is composed with the same root, fs, journal and clock. `storm_producer` keeps its signature and stays the composer that tests call with an explicit root.
- compatibility: `storm_producer(root=, fs=, journal=, clock=)` is unchanged. Tests that wrap `daemon.storm_producer` still see every production composition, because the builder looks it up on the module at call time. Their `journal`, `fs` and `clock` keyword assertions still hold, because the builder forwards those three unchanged.
- acceptance: the builder returns a Box whose root is `config.state_dir / BOX_DIR`. No `clutch/` module other than `daemon.py` calls `storm_producer`.
- tests: new unit test for the builder, and an added case in the projection-owner source scan
- post-merge source of truth: clutch/daemon.py

## Scope in / Scope out
Scope in:
- Add `storm_producer_for_config` to `clutch/daemon.py`. It computes `root = config.state_dir / BOX_DIR` and calls `storm_producer(root=root, fs=fs, journal=journal, clock=clock)`. Import `BOX_DIR` from `clutch.box` in `daemon.py`.
- Replace the 15 direct calls listed in Goal with the builder. Each call's `from clutch.daemon import ...` line imports the builder in place of `storm_producer`. At `clutch/stages.py` around line 1110, `flake_detection` stays imported. Remove `BOX_DIR` imports in these files only when the replacement leaves them unused.
- In `tests/integration/test_projection_helpers_source.py`, add a violation rule: a call to `storm_producer`, as a name or as an attribute, in any `clutch/` file other than `daemon.py` is a violation. Add matching rows to `test_scan_rejects_copies_and_permits_exclusions`.
- Add a new unit test file for the builder, using `tmp_path` and fakes.

Scope out:
- No change to `storm_producer`, `Box` or `StormBreaker` behavior.
- No change to tests that call `storm_producer` with an explicit root.
- `EngineLog` construction in `Driver.from_config` is `projection-leftovers`, not this ticket.

## Scope fence
- clutch/daemon.py
- clutch/__main__.py
- clutch/driver.py
- clutch/retro.py
- clutch/runner.py
- clutch/stages.py
- clutch/triage.py
- tests/integration/test_projection_helpers_source.py
- tests/unit/test_storm_producer_builder.py

## Acceptance criteria
1. `storm_producer_for_config(SimpleNamespace(state_dir=tmp_path), fs=fs, journal=journal, clock=clock).root` equals `tmp_path / "box"`, not `tmp_path`, checked by `./dev.py test tests/unit/test_storm_producer_builder.py`.
2. The builder forwards `fs`, `journal` and `clock` to `storm_producer`, so `box.fs is fs`. A call recorded on a monkeypatched `daemon.storm_producer` shows the same three objects, checked by `./dev.py test tests/unit/test_storm_producer_builder.py`.
3. A search of `clutch/*.py` outside `daemon.py` finds no call to `storm_producer`, so `test_projection_owners` fails on the old 15-site tree. It also rejects `storm_producer(root=r, fs=f, journal=j, clock=c)` in `other.py` and allows the same call in `daemon.py`, checked by `./dev.py test tests/integration/test_projection_helpers_source.py`.
4. Existing storm composition tests still pass, including the production-reachability hook that wraps `daemon.storm_producer`, checked by `./dev.py test tests/integration/test_storm_producer.py tests/integration/test_storm_notification_activation.py tests/integration/test_box.py`.
5. The full suite passes, checked by `./dev.py test`.

## Verification
```
./dev.py test tests/unit/test_storm_producer_builder.py tests/integration/test_projection_helpers_source.py tests/integration/test_storm_producer.py tests/integration/test_storm_notification_activation.py
./dev.py test
```

## Definition of rejected
Any production site outside `clutch/daemon.py` still calls `storm_producer` directly. A call site changes which Box root, fs, journal or clock it composes. The builder is added without the source-scan rule. Tests are edited to hide a behavior change.

## Time budget
- expected: 20m
- stuck: 40m
