---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- integration-io-guard

## Runs before
- test-rules-prompt
- shared-fakes-guard
- shared-git-fake-integration
- shared-git-fake-unit-6
- shared-git-fake-unit-5
- shared-git-fake-unit-4
- shared-git-fake-unit-3
- shared-git-fake-unit-2
- shared-git-fake
- shared-serve-rig-config
- shared-review-script
- check-rerun-failed-only
- serve-flaky-tests-deterministic
- reconcile-spares-confirming-draft
- flake-fix-jumps-queue
- preflight-once-per-session
- serve-contains-dispatch-exception
- check-meta-fill-nested-stage
- supervisor-orders-by-depends
- gemini-provider-configured
- retry-keeps-prior-branch

## Context
- clutch/docs/host-authoring.md#Unit and integration tests
- tests/integration/test_unit_io_rule.py
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_meta_headers.py

## On-demand
- clutch/specs/implement.md
- clutch/specs/retro.md
- tests/integration/test_retro.py

## Goal / Why
The shipped test rules restrict only unit tests and send everything else to the integration suite. `clutch/specs/implement.md` defines an integration test as one that checks "a process boundary or real files"; `clutch/docs/host-authoring.md` says "Place a test that needs a repo file, a process, or the network under `tests/integration/`"; and the retro `unit-io` repair in `clutch/specs/retro.md` ends "or move it to integration". Agents followed these rules: on 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk during every Check. Agents also leave scratch files in `/tmp` (for example `/tmp/clutch-index-base-verify`, 581 MB, and `/tmp/clutch-meta-base-check`). `integration-io-guard` blocks this mechanically in this repo; this ticket makes the written rules say the same thing, so Implement, Author and retro stop producing such tests and scratch files.

When this ticket is done, the shipped rules say: an integration test checks a seam through in-memory fakes and simulators and never writes to disk, starts a process, runs git, or opens a network connection or an on-disk database; only a test whose subject is a real I/O function touches real disk or processes, and the host lists its file in an explicit allowlist; test temporary files and agent scratch files never go to `/tmp` or another system-wide directory, and Implement writes scratch files only under `.clutch/scratch/` in its worktree. The unit-test rules are unchanged.

Rule homes: these are rules every host should follow about how tests are written and where an agent writes scratch, so they live in the shipped prompt specs and the shipped authoring guide, which reach every host. They do not go in `CORE_TEMPLATE` (8191 of its 8192-byte cap is used) or only in this repo's `CLAUDE.md` and `AGENTS.md`.

## Boundary contract
### Shipped test rules
- disposition: replace
- owner: clutch/specs/implement.md, clutch/specs/retro.md, clutch/docs/host-authoring.md
- consumers: the Implement, Retro and Author stages and every host reading the authoring guide; the pinning tests tests/unit/test_specs.py, tests/integration/test_unit_io_rule.py, tests/integration/test_specs_delimiter_note.py, tests/integration/test_implement_spec_meta_headers.py, tests/integration/test_retro.py
- observable change: the integration-test definition forbids disk writes, processes, git, network and on-disk databases except allowlisted real-I/O tests; the retro `unit-io` repair no longer suggests moving a test to integration; Implement scratch goes under `.clutch/scratch/`, never `/tmp`
- compatibility: the unit-test rule text is unchanged; old contract "an integration test checks a process boundary or real files" is replaced in the same change in every copy, and the pinning tests move to the new text
- acceptance: the new phrases are present and the old phrases are absent in each owner
- tests: tests/unit/test_specs.py and tests/integration/test_unit_io_rule.py
- post-merge source of truth: clutch/specs/implement.md, clutch/specs/retro.md, clutch/docs/host-authoring.md

## Scope in / Scope out
Scope in:
- `clutch/specs/implement.md`: replace the two sentences beginning "An integration test checks a seam" with exactly: "An integration test checks a seam: an API, a command-line interface or how modules compose. It drives the code through in-memory fakes and simulators and never writes to disk, starts a process, runs git, or opens a network connection or an on-disk database, so it finishes in bounded time and runs in parallel with other tests. Only a test whose subject is a real I/O function (a filesystem, process, git or journal wrapper) touches real disk or processes, and its file must be in the host's explicit allowlist." After that paragraph add one sentence: "Write scratch files only under `.clutch/scratch/` in your worktree, never in `/tmp` or another system-wide directory." Bump `version` to the next minor above the version on main.
- `clutch/specs/retro.md`: in the `unit-io` bullet, replace "inject a seam or fake, call the library instead of shelling out, or move it to integration." with "inject a seam or fake, or call the library instead of shelling out." Bump `version` to the next minor above the version on main.
- `clutch/docs/host-authoring.md` section `## Unit and integration tests`: replace the sentence "Place a test that needs a repo file, a process, or the network under `tests/integration/` and fence that file." with "Place a test that reads a repo file under `tests/integration/` and fence that file. An integration test never writes to disk, starts a process, runs git, or opens a network connection or an on-disk database; it drives the code through in-memory fakes. Only a test whose subject is a real I/O function touches real disk or processes, and its file is in the host's explicit allowlist (in clutch's own repo, `REAL_IO_TESTS` in `tests/integration/conftest.py`). Test temporary files never go to `/tmp`." In the coverage paragraph, replace "and moves only the real disk, process, or network checks to `tests/integration/`." with "and covers the real disk, process, or network site only in an allowlisted real-I/O test." Nothing else in the guide changes.
- Pinning tests, updated to the new text and versions: `tests/unit/test_specs.py` (the implement integration sentence and the implement version pins), `tests/integration/test_unit_io_rule.py` (the authoring-guide phrases, plus a check that "or move it to integration" is absent from the retro task and "a process boundary or real files" is absent from the implement task), `tests/integration/test_specs_delimiter_note.py` and `tests/integration/test_implement_spec_meta_headers.py` (versions), `tests/integration/test_retro.py` (the retro `spec_version` in the provenance assertion).

Scope out:
- `CORE_TEMPLATE`, the repo agent rule files, the review prompt spec, and the unit-test rule sentences.
- Any code, guard or test-suite change (`integration-io-guard`, `integration-disk-io-skip`, `test-tmp-in-checkout`).
- Editing `tickets/test-rules-prompt`; this ticket only runs before it.

## Scope fence
- clutch/specs/implement.md
- clutch/specs/retro.md
- clutch/docs/host-authoring.md
- tests/unit/test_specs.py
- tests/integration/test_unit_io_rule.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_implement_spec_meta_headers.py
- tests/integration/test_retro.py

## Acceptance criteria
1. `tests/unit/test_specs.py` asserts the implement task contains the new integration-test sentences and the `.clutch/scratch/` sentence exactly as written in Scope in, and the implement version is the bumped value (the old "process boundary or real files" sentence fails it), run by `./dev.py test tests/unit/test_specs.py`.
2. `tests/integration/test_unit_io_rule.py` asserts the authoring guide contains each new sentence from Scope in, does not contain "Place a test that needs a repo file, a process, or the network", the retro task does not contain "or move it to integration", and the implement task does not contain "a process boundary or real files", run by `./dev.py test tests/integration/test_unit_io_rule.py`.
3. `tests/integration/test_specs_delimiter_note.py`, `tests/integration/test_implement_spec_meta_headers.py` and `tests/integration/test_retro.py` pass with the bumped implement and retro versions, run by `./dev.py test tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_retro.py`.
4. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_specs.py tests/integration/test_unit_io_rule.py
./dev.py test tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_meta_headers.py tests/integration/test_retro.py
./dev.py test
```

## Definition of rejected
- The unit-test rule sentences change, or the new text allows integration tests to write disk, start processes or run git outside an allowlist.
- A rule is added to `CORE_TEMPLATE` or the repo agent rule files.
- A pinning test is deleted instead of updated.

## Time budget
- expected: 20m
- stuck: 40m
