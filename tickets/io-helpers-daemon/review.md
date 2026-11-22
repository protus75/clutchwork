# Review: snag

The extraction and import rewiring are complete, but three things are wrong: CoreRig's default config changed, LiveDrain dropped the checks it used to make, and the admission hub keeps an unused closure function.

## Findings

- [logic] tests/daemon_helpers.py:42 CoreRig's default changed from `config=CONFIG`, which in the hub was `tests.integration.test_providers.CONFIG` (claude/codex providers, routing, `state_dir: state`), to `config=CLI_CONFIG` from `tests.cli_helpers`. The ticket says to keep each moved name's signature unless a change is named, and none is named for CoreRig. Callers that rely on the default provider config now get a different one: `test_provider_cooldown_failover.py` (lines 165, 197, 291, 385), `test_evidence_envelope.py:35`, the `test_watchdog*` rigs and many hub tests call `CoreRig(tmp_path)` and expect the claude/codex providers and routing. (do instead: Keep the old default. Import the providers config under a distinct name (for example `from tests.integration.test_providers import CONFIG as PROVIDERS_CONFIG`, or an identical `build_config(...)` value from a shared, unskipped module) and use it as CoreRig's `config` default.)
- [logic] tests/daemon_helpers.py:254 LiveDrain's write hook no longer makes the checks the hub's `Files.write` made on every `control/active.json` discovery write. The old hook checked that a contending `Lockfile(...).acquire()` raises `LockHeld`, that `trace[0] == "lock"` with no `unlock` yet, and that a non-null `hold_id` has an accepted control decision in the journal. Every LiveDrain-based test, in the hub and in the kill tests, silently loses these checks, which the ticket's Definition of rejected forbids ("a hub test is ... weakened"). The trace and hold-acceptance checks need only the in-memory trace and FakeJournal, and the lock contender works under the caller's `tmp_path`. (do instead: Put the checks back in `written()`: the lock-contender `pytest.raises(LockHeld)` check, `assert self.trace[0] == "lock" and "unlock" not in self.trace`, and the hold_id-accepted check against `self.checkout.journal.read()`, all before the trace append.)
- [logic] tests/integration/test_daemon_admission.py:204 `import_closure` was renamed to `admission_import_closure`, but its only caller, `assert_reachable`, moved to `tests/daemon_helpers.py` with its own inlined copy of the same closure loop. The renamed function now has no caller in the hub, and the closure logic exists twice. (do instead: Delete `admission_import_closure` from the hub, since its logic now lives only in `daemon_helpers.assert_reachable`, along with any import (for example `ast`) that is unused once it is gone.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "0972eef336d290c883092b12a22496db576d8997",
  "stem": "io-helpers-daemon",
  "reviewed_sha": "0972eef336d290c883092b12a22496db576d8997",
  "summary": "The extraction and import rewiring are complete, but three things are wrong: CoreRig's default config changed, LiveDrain dropped the checks it used to make, and the admission hub keeps an unused closure function.",
  "findings": [
    {
      "code": "logic",
      "path": "tests/daemon_helpers.py",
      "line": 42,
      "message": "CoreRig's default changed from `config=CONFIG`, which in the hub was `tests.integration.test_providers.CONFIG` (claude/codex providers, routing, `state_dir: state`), to `config=CLI_CONFIG` from `tests.cli_helpers`. The ticket says to keep each moved name's signature unless a change is named, and none is named for CoreRig. Callers that rely on the default provider config now get a different one: `test_provider_cooldown_failover.py` (lines 165, 197, 291, 385), `test_evidence_envelope.py:35`, the `test_watchdog*` rigs and many hub tests call `CoreRig(tmp_path)` and expect the claude/codex providers and routing.",
      "paved_road": "Keep the old default. Import the providers config under a distinct name (for example `from tests.integration.test_providers import CONFIG as PROVIDERS_CONFIG`, or an identical `build_config(...)` value from a shared, unskipped module) and use it as CoreRig's `config` default.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/daemon_helpers.py",
      "line": 254,
      "message": "LiveDrain's write hook no longer makes the checks the hub's `Files.write` made on every `control/active.json` discovery write. The old hook checked that a contending `Lockfile(...).acquire()` raises `LockHeld`, that `trace[0] == \"lock\"` with no `unlock` yet, and that a non-null `hold_id` has an accepted control decision in the journal. Every LiveDrain-based test, in the hub and in the kill tests, silently loses these checks, which the ticket's Definition of rejected forbids (\"a hub test is ... weakened\"). The trace and hold-acceptance checks need only the in-memory trace and FakeJournal, and the lock contender works under the caller's `tmp_path`.",
      "paved_road": "Put the checks back in `written()`: the lock-contender `pytest.raises(LockHeld)` check, `assert self.trace[0] == \"lock\" and \"unlock\" not in self.trace`, and the hold_id-accepted check against `self.checkout.journal.read()`, all before the trace append.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/integration/test_daemon_admission.py",
      "line": 204,
      "message": "`import_closure` was renamed to `admission_import_closure`, but its only caller, `assert_reachable`, moved to `tests/daemon_helpers.py` with its own inlined copy of the same closure loop. The renamed function now has no caller in the hub, and the closure logic exists twice.",
      "paved_road": "Delete `admission_import_closure` from the hub, since its logic now lives only in `daemon_helpers.assert_reachable`, along with any import (for example `ast`) that is unused once it is gone.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
