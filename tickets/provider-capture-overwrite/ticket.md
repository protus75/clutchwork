---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Context
- chupa/providers.py::CliAdapter.__init__
- chupa/providers.py::CliAdapter.invoke
- chupa/seams.py::FileSystem
- chupa/seams.py::LocalFileSystem
- chupa/runner.py::harvest
- docs/how-chupa-works.md#10.1
- tickets/provider-capture-overwrite/evidence/capture-overwrite-counts.txt
- tickets/provider-capture-overwrite/evidence/provider_capture_overwrite-at-base.txt
- tickets/provider-capture-overwrite/evidence/repro_provider_capture_overwrite.py
- tests/regress_drain_deadline.py
- tests/integration/test_providers.py::FakeExec
- tests/integration/test_providers.py::config
- tests/integration/test_providers.py::llm
- tests/integration/test_providers.py::req
- tests/integration/test_providers.py::claude_ok

## On-demand
- tests/unit/test_preflight_parallel.py

## Goal / Why
Every model call's raw transcript (`prompt.md`, `events.jsonl`, `stderr.txt`) is written to `<state_dir>/spools/providers/<stem>/<provider>-NNNN/`. `NNNN` comes from `CliAdapter._seq`, a counter that starts at 0 when the adapter is built (`chupa/providers.py::CliAdapter.__init__`) and increments per call (`CliAdapter.invoke`). One adapter lives per engine process. So when a stem's calls happen in a later process (a retry in the next drain, a re-offer, a rework, a second `triage` pass), the new process writes `claude-0001` again and replaces the earlier process's transcript.

Measured on this repo's state at `328d07d9` (`evidence/capture-overwrite-counts.txt`): the journal records 3,960 model calls and 2,298 capture directories hold an `events.jsonl`; 1,662 transcripts are gone. `triage` made 467 calls and has 282 captures; `author` 336 and 157. The reproducer in `evidence/repro_provider_capture_overwrite.py`, run at `328d07d9` (`evidence/provider_capture_overwrite-at-base.txt`), builds two `ProviderLLM` instances on one state directory, makes one call each for ticket `t-1`, and finds one file, `t-1/claude-0001/events.jsonl`, holding only the second run's text.

These transcripts are what `chupa/runner.py::harvest` tails into `harvest.json` for diagnosis, and what a person opens to see what an agent did. Losing an earlier attempt's transcript removes the record of the attempt that failed.

When this ticket is done, a process continues a stem's numbering from the highest capture directory already on disk for that stem, so no call's transcript is written over another's. The directory name format `<provider>-NNNN` and the three file names inside it do not change.

## Scope in / Scope out
- In: `chupa/seams.py`. The `FileSystem` protocol gains `entries(path: Path) -> list[str]`: the names directly inside a directory, sorted, `[]` when the directory does not exist. `LocalFileSystem.entries` implements it with `os.listdir`. Nothing else in the protocol changes.
- In: `chupa/providers.py`.
  - A pure module-level helper `capture_sequence(names: Iterable[str], provider: str) -> int` returns one more than the highest `NNNN` among names matching `<provider>-NNNN` (exactly four digits), and `1` when none matches. Names of other providers and names of any other shape are ignored.
  - `CliAdapter` replaces the single `_seq` counter with a per-stem map `_seq: dict[str, int]`. In `invoke`, the first call for a stem in this process sets its number from `capture_sequence(self._fs.entries(self._capture_dir / stem), self.provider.name)`; every later call for that stem adds one. `stem` is `req.ticket or req.surface`, as today. The directory name, `prompt.md`, `events.jsonl`, and `stderr.txt` are unchanged.
  - Numbering becomes per stem: in one process, the first capture for stem A and the first for stem B are both `-0001`. Today they share one counter (`-0001`, `-0002`). No reader depends on the shared numbering: `harvest` picks the newest `events.jsonl` by mtime.
- In: `tests/unit/test_capture_sequence.py` (new): `capture_sequence` with in-memory name lists; no disk.
- In: `tests/integration/test_provider_capture_overwrite.py` (new): the reproducer as a pytest test, using the `config`, `llm`, `FakeExec`, `claude_ok`, and `req` helpers from `tests/integration/test_providers.py`, plus the per-stem numbering case.
- In: `tests/regress_provider_capture_overwrite.py` (new): the carried reproducer in the shape of `tests/regress_drain_deadline.py`. It runs `pytest` on `tests/integration/test_provider_capture_overwrite.py` with stdout redirected to stderr and prints the one `regression_result` line.
- In: `tests/unit/test_preflight_parallel.py`. Its `MemoryFS` gains `entries` returning `[]`, because preflight probes reach `invoke` and `invoke` now lists the capture directory.
- In: `tests/integration/test_effects.py`. `FakeFS` (line 35) gains `entries(path)` returning `[]`, so the `isinstance(fs, FileSystem)` assertion at line 65 still holds against the runtime-checkable protocol.
- In: `tests/integration/test_daemon_composition.py`. `ScriptFS` (line 37) gains `entries(path)` returning the sorted names of its in-memory files directly under `path`, or `[]`, because `CoreRig` hands it to the adapters and runs calls through `invoke`. No test is added to this file.
- In: `tests/unit/test_probe_verb.py`. The `Mock()` filesystem at line 18 sets `fs.entries.return_value = []` so `capture_sequence` receives a list; the assertions are unchanged.
- In: `docs/how-chupa-works.md` section 10.1, the `spools/` row: after "`spools/providers/` holds raw CLI captures", add that a stem's capture numbers continue from the highest already on disk, so a later process never overwrites an earlier capture.
- Out: keying captures by the journal's call key, which is the roadmap's `evidence-envelope` (`docs/roadmap.md` row 29) and replaces this directory layout. Moving captures anywhere else. `spools/probe/` (one probe set per process; its own `capture_dir`). `harvest`'s reader. The `evidence/` files of this ticket.

## Scope fence
- chupa/providers.py
- chupa/seams.py
- docs/how-chupa-works.md
- tests/unit/test_capture_sequence.py
- tests/unit/test_preflight_parallel.py
- tests/unit/test_probe_verb.py
- tests/integration/test_effects.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_provider_capture_overwrite.py
- tests/regress_provider_capture_overwrite.py

## Acceptance criteria
1. `tests/unit/test_capture_sequence.py` covers, without disk: no names returns `1`, not `0`; `["claude-0003", "claude-0001"]` with provider `claude` returns `4`, not `3` (count plus one); `["claude-0005"]` returns `6`, not `2`; `["codex-0009"]` with provider `claude` returns `1`; `["claude-x", "README", "claude-00010"]` returns `1`.
2. `tests/integration/test_provider_capture_overwrite.py` builds two `ProviderLLM` instances on one state directory and makes one `review` call each for ticket `t-1`; afterwards `spools/providers/t-1/claude-0001/events.jsonl` holds the first call's reply text and `spools/providers/t-1/claude-0002/events.jsonl` the second's, and no other `events.jsonl` exists under `t-1`. The wrong result it rules out is one file holding the second text.
3. The same file: one `ProviderLLM` instance making one call for ticket `t-1` and one for ticket `t-2` writes `t-1/claude-0001` and `t-2/claude-0001`, not `t-2/claude-0002`.
4. `uv run python tests/regress_provider_capture_overwrite.py` prints exactly `{"regression_result": "pass"}` and exits 0 on the branch head, and prints `{"regression_result": "defect"}` with exit 1 on the merge base with the carried files copied over it.
5. `docs/how-chupa-works.md` section 10.1's `spools/` row contains the sentence about numbering continuing across processes.
6. `./dev.py test` exits 0, including `tests/unit/test_preflight_parallel.py` unchanged in its assertions.

## Verification
```
./dev.py test
```

## Definition of rejected
- A second process's capture for a stem reuses a directory name an earlier process wrote under `spools/providers/<stem>/`.
- The capture directory name format `<provider>-NNNN` or the file names inside it change.
- `chupa/providers.py` reads a directory through anything other than the `FileSystem` seam.
- Captures are written anywhere other than `<state_dir>/spools/providers/`.

## Time budget
- expected: 30m
- stuck: 60m

## Regression
```
uv run python tests/regress_provider_capture_overwrite.py
```
- carries: tests/regress_provider_capture_overwrite.py
- carries: tests/integration/test_provider_capture_overwrite.py
