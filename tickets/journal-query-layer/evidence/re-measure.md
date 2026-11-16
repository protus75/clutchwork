# Journal re-measurement: drain start and `clutch status`

Roadmap row 35, the start gate of row 36 (`journal-query-layer`) and of the conditional 0.4.0 window (`docs/roadmap.md` section 1; `docs/journal-sql-refactor-plan.md`, Problem and Release protocol). An agent took this capture on 2026-11-16.

- **Commit measured:** `80a2b6cfe052eac9773a5464fdd21b1cd618a134` (main, "clutch(roadmap): author active-slot-single-owner"). The commits that landed while this was written, through `2f88001f`, change only `tickets/`, so the measured code is still current.
- **Journal:** 16 segments, 29,841 events (one per line, no torn tail), 17,818,214 bytes (17.8 MB). Copied from `.clutch/state/journal/` at 2026-11-16T10:01:12Z.
- **Host:** WSL2 Linux, 20 cores, Python 3.14.6 (the clutch venv, `uv sync --frozen`).
- **Threshold** (plan, Problem): "record the share of wall time in journal reads. If it is under a quarter, the window slides and this plan waits for the next measurement." Roadmap section 1 gate for 0.4.0: "re-measurement shows a drain start or `status` still dominated by journal reads".

**Verdict: journal reads still dominate: the window runs.**

| Profile | Wall time, no profiler | Journal reads | Reads + folds | cProfile wall | cProfile read share |
|---|---|---|---|---|---|
| Drain start, up to first admission | 1.74-2.28s (4 timed runs) | 20.5%, 25.4%, 27.4%, 29.3% (timed); 25.1-27.2% (sampler) | 55.7-57.6% (sampler) | 3.85s | 24.6% (0.942 of 3.826s) |
| `clutch status` | 0.42s process, 0.35-0.38s in process | 51.2-52.1% (sampler) | 59.9-61.3% (sampler) | 0.81s | 52.4% (0.391 of 0.746s) |

`status` is about half journal read, well over the threshold. On reads alone the drain start sits at the threshold (median about 26%). With folds counted, it is over half.

## Method

This run reproduces the 2026-11-11 measurement (`tickets/journal-incremental-read/evidence/drain-start-journal-rereads.txt`) on current main. The live drain in the real checkout was never touched.

- **Copy.** `git clone --no-hardlinks` of the checkout at `80a2b6cf` into a scratch directory, with its own venv. `.clutch/state` was copied journal first, without `worktrees/` and without the live drain's `clutch.lock`. Every drain run started from the same pristine copy of that state.
- **Drain start.** A harness calls `clutch.__main__.main(["drain"])` on the copy. Three things are patched out, the same three as on 2026-11-11: `reconcile`, `intake`, and the provider preflight probes (`ProviderLLM.preflight` returns no problems). `ProviderLLM.call` raises, so no model call can happen. `_Drain._run_one` is replaced by a stop, so the run ends where it would admit its first ticket. Everything else is real: the lock, control publish, timers, pipeline `bind`, the retro check, scan, and `_select`. Every run reached admission: `would dispatch release-at-gate (reoffer=True)`. In the copied journal, the live drain's in-flight run is an interrupted run.
- **Status.** `python -m clutch status`, unpatched.
- **Instruments.**
  - (1) `python -m cProfile` for the excerpts below. It inflates the drain start about 1.9x.
  - (2) `time.perf_counter` wrappers on `Journal.read`, `read_segments`, and `append`, with no profiler running ("timed").
  - (3) A wall-clock stack sampler (0.5 ms interval) that splits the run into disjoint buckets:
    - journal read: a frame inside `Journal.read` or `read_segments`.
    - journal fold: the innermost `clutch/` frame holds an `Event` or an event list and is executing itself, with no library frames below it.
    - box files, git/subprocess, imports, and event-loop wait.
- **Definitions.** "Journal reads" is time inside `clutch/journal.py` `read()` and `read_segments()`: the cold parse plus the cached-list copies. "Folds" are the Python loops over the returned events, which are the status and drain projections: `control.decisions`, the `Effects` startup scan and `_recorded`, `caps.lineage`, storm history and evidence, the retro scans, `thresh.fold_breakers`, `status.project`, `last_states`, and `reject_queue`.

## Change since 2026-11-11 (`bf121ef9`)

| | 2026-11-11 | 2026-11-16 |
|---|---|---|
| Journal | about 24k events, 12 segments, 12 MB | 29,841 events, 16 segments, 17.8 MB |
| `Journal.read()` calls in a drain start | 491 | 152 profiled, 110-117 timed |
| Cost of one `read()` | 0.13s, a full re-parse every call | 0.18s cold, once per `Journal` instance; 0.45 ms cached |
| Profiled drain start to admission | 164.2s, 157.0s of it in `read()` (96%) | 3.6s from `main()`, 0.94s of it in `read()` (24.6%) |
| Live drain starts, `engine_start` to first `stage_start` (engine.log) | 82-355s, typically 85-100s | median 10.3s over the last 20 starts: provider preflight 5-27s (median about 6s), the rest median 4.2s |

## Where the remaining journal time goes

- **Cold parse.** It costs 0.18s per `Journal` instance (29,841 lines). Inside `_parse_line`, `json.loads` takes 44% and the timestamp pin check (`_is_pinned_ts`, which renders each `ts` again) takes 19%. Envelope checks take the rest.
- **`status`.** It calls `read()` once, so it makes exactly one cold parse, and that parse is half its wall time.
- **Drain start, second parse.** The drain start parses the journal twice (59,682 `_parse_line` calls, which is 2 × 29,841). `Driver.from_config` (`clutch/driver.py:187`) builds its own `Journal(config.state_dir, clock)`. `Driver.__init__` then builds `Effects(journal)`, whose startup scan reads the whole journal. `runner.bind` (`clutch/runner.py:140-141`) then replaces both with the checkout's journal. The extra parse costs about 0.18s, roughly 9-10 points of the drain-start share. Without it, reads alone would be about 17% of the drain start (0.29 of about 1.7s; an estimate, not measured).
- **Cached reads.** The other 108-150 `read()` calls in a drain start hit the cache. Each still copies a 29,841-item list (about 0.45 ms).
- **Folds.** The biggest fold sites in the drain start come from the control polling loop, which runs every 0.1s while the retro check runs:
  - `control.decisions`, called from `_fold` and `settle_admissions` (2,860 calls, 1.65M `dict.get`).
  - an `Effects(self.journal)` built for each admission in `control.settle_admissions` (30 calls, each a full-journal set build).
  - `caps.lineage` and `caps.spent` during `_select`.
  - the storm history and evidence scans.

## Notes for the decision

- **The verdict follows the plan's share rule.** In absolute terms the trigger's cost fell about 80x. A drain start now reaches admission in about 2s and `status` takes about 0.4s. Provider preflight probes, not the journal, are the largest part of a live drain start.
- **What fixing the second parse changes.** Removing the redundant parse in `Driver.from_config` would bring the drain start's read-only share to about 17%. It would not change `status`, whose one cold parse is the read itself. A DuckDB bulk load replaces that cold parse; it does not remove it.
- **Not journal: Suggestion Box rereads.** `box.messages` reads and validates every Suggestion Box file (536) on each of 49 `emit_proposals` calls during the retro check. That is about 0.48s, a quarter of the drain start (sampler box-files bucket).

## Profile excerpts

### Drain start, cProfile (`python -m cProfile -o drain.prof drain_start.py <copy>`)

```
would dispatch release-at-gate (reoffer=True)
elapsed: process-start->admission 3.850s; main()->admission 3.613s; imports 0.237s
total profiled time (sum tottime): 3.826s
Journal.read: 152 calls, cumtime 0.942s
Journal.read_segments: 2584 calls total, 0.000s from callers other than read()
  journal._parse_line: ncalls 59682, tottime 0.179s, cumtime 0.731s
  journal._parse_segment: ncalls 30, tottime 0.007s, cumtime 0.731s
  journal._parse_complete_lines: ncalls 152, tottime 0.002s, cumtime 0.047s
  journal._read_active: ncalls 152, tottime 0.003s, cumtime 0.055s
journal read time (read + direct read_segments): 0.942s = 24.6% of profiled total

callers of Journal.read (ncalls, cumtime):
     32    0.427s  effects.py:18(__init__)
     10    0.395s  storm.py:45(_history)
     30    0.038s  control.py:185(_fold)
     30    0.034s  effects.py:49(_recorded)
     16    0.017s  retro.py:308(emit_proposals)
     15    0.014s  control.py:268(settle_admissions)
     10    0.008s  storm.py:82(_evidence)
      3    0.002s  thresh.py:79(fold_breakers)
      2    0.002s  retro.py:396(__call__)
      2    0.002s  drain.py:384(run)
      1    0.001s  drain.py:472(_scan)
      1    0.001s  timers.py:69(reconstruct)

Top 15 cumulative:
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    368/1    0.022    0.000    3.859    3.859 {built-in method builtins.exec}
        1    0.000    0.000    3.859    3.859 drain_start.py:1(<module>)
        1    0.000    0.000    3.622    3.622 clutch/__main__.py:332(main)
        2    0.000    0.000    3.594    1.797 asyncio/runners.py:170(run)
        6    0.000    0.000    3.594    0.599 asyncio/base_events.py:683(run_until_complete)
        2    0.000    0.000    3.594    1.797 asyncio/runners.py:88(run)
        6    0.000    0.000    3.594    0.599 asyncio/base_events.py:672(run_forever)
     1281    0.005    0.000    3.593    0.003 asyncio/base_events.py:1976(_run_once)
     2924    0.002    0.000    3.502    0.001 asyncio/events.py:92(_run)
     2924    0.003    0.000    3.500    0.001 {method 'run' of '_contextvars.Context' objects}
       21    0.000    0.000    1.476    0.070 clutch/drain.py:216(drain)
      129    0.034    0.000    1.164    0.009 clutch/retro.py:396(__call__)
      147    0.041    0.000    1.107    0.008 clutch/retro.py:308(emit_proposals)
      152    0.057    0.000    0.942    0.006 clutch/journal.py:229(read)
     2584    0.036    0.000    0.885    0.000 clutch/journal.py:197(read_segments)

Top 15 cumulative, clutch/ only:
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    3.622    3.622 clutch/__main__.py:332(main)
       21    0.000    0.000    1.476    0.070 clutch/drain.py:216(drain)
      129    0.034    0.000    1.164    0.009 clutch/retro.py:396(__call__)
      147    0.041    0.000    1.107    0.008 clutch/retro.py:308(emit_proposals)
      152    0.057    0.000    0.942    0.006 clutch/journal.py:229(read)
     2584    0.036    0.000    0.885    0.000 clutch/journal.py:197(read_segments)
       49    0.046    0.001    0.866    0.018 clutch/box.py:194(messages)
    59682    0.179    0.000    0.731    0.000 clutch/journal.py:288(_parse_line)
       30    0.007    0.000    0.731    0.024 clutch/journal.py:278(_parse_segment)
    56234    0.019    0.000    0.706    0.000 clutch/journal.py:285(<genexpr>)
       10    0.062    0.006    0.605    0.061 clutch/storm.py:82(_evidence)
       13    0.000    0.000    0.592    0.046 clutch/drain.py:622(control)
       19    0.001    0.000    0.592    0.031 clutch/drain.py:384(run)
       32    0.112    0.004    0.539    0.017 clutch/effects.py:18(__init__)
        6    0.000    0.000    0.518    0.086 clutch/daemon.py:197(storm_holds)
```

### `clutch status`, cProfile (`python -m cProfile -o status.prof -m clutch status`)

```
total profiled time (sum tottime): 0.746s   (process wall 0.81s)
Journal.read: 1 calls, cumtime 0.391s
  journal._parse_line: ncalls 29841, tottime 0.091s, cumtime 0.365s
    -> json.loads 0.160s, _is_pinned_ts 0.071s (render_ts 0.041s)
  journal._parse_segment: ncalls 15, tottime 0.003s, cumtime 0.367s
  journal._read_active: ncalls 1, tottime 0.000s, cumtime 0.022s
journal read time (read + direct read_segments): 0.391s = 52.4% of profiled total
callers of Journal.read: 1 call, 0.391s, __main__.py:1030(_status)

Top 15 cumulative:
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    361/1    0.021    0.000    0.762    0.762 {built-in method builtins.exec}
        1    0.000    0.000    0.762    0.762 <string>:1(<module>)
        1    0.000    0.000    0.762    0.762 <frozen runpy>:206(run_module)
        1    0.000    0.000    0.761    0.761 <frozen runpy>:65(_run_code)
        1    0.006    0.006    0.761    0.761 clutch/__main__.py:1(<module>)
        1    0.000    0.000    0.524    0.524 clutch/__main__.py:332(main)
        1    0.000    0.000    0.501    0.501 asyncio/runners.py:170(run)
        3    0.000    0.000    0.501    0.167 asyncio/base_events.py:683(run_until_complete)
        1    0.000    0.000    0.501    0.501 asyncio/runners.py:88(run)
        3    0.000    0.000    0.501    0.167 asyncio/base_events.py:672(run_forever)
      280    0.001    0.000    0.501    0.002 asyncio/base_events.py:1976(_run_once)
      607    0.000    0.000    0.488    0.001 asyncio/events.py:92(_run)
      607    0.001    0.000    0.488    0.001 {method 'run' of '_contextvars.Context' objects}
       33    0.001    0.000    0.484    0.015 clutch/__main__.py:1030(_status)
        1    0.000    0.000    0.391    0.391 clutch/journal.py:229(read)

Top 15 cumulative, clutch/ only:
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.006    0.006    0.761    0.761 clutch/__main__.py:1(<module>)
        1    0.000    0.000    0.524    0.524 clutch/__main__.py:332(main)
       33    0.001    0.000    0.484    0.015 clutch/__main__.py:1030(_status)
        1    0.000    0.000    0.391    0.391 clutch/journal.py:229(read)
       17    0.001    0.000    0.390    0.023 clutch/journal.py:197(read_segments)
       15    0.003    0.000    0.367    0.024 clutch/journal.py:278(_parse_segment)
    29841    0.091    0.000    0.365    0.000 clutch/journal.py:288(_parse_line)
    28117    0.010    0.000    0.354    0.000 clutch/journal.py:285(<genexpr>)
        1    0.000    0.000    0.171    0.171 clutch/ask.py:1(<module>)
        1    0.000    0.000    0.110    0.110 clutch/specs/__init__.py:1(<module>)
        1    0.004    0.004    0.073    0.073 clutch/status.py:187(project)
    29841    0.018    0.000    0.071    0.000 clutch/journal.py:313(_is_pinned_ts)
        1    0.000    0.000    0.060    0.060 clutch/runner.py:1(<module>)
    29841    0.013    0.000    0.041    0.000 clutch/journal.py:140(render_ts)
        1    0.000    0.000    0.033    0.033 clutch/artifacts.py:1(<module>)
```

### No-profiler runs

```
drain start, perf_counter wrappers only (4 runs, each from the pristine state copy):
  run 1: admission at 2.156s; Journal.read 110 calls 0.442s = 20.5%
  run 2: admission at 1.743s; Journal.read 110 calls 0.478s = 27.4%
  run 3: admission at 1.844s; Journal.read 117 calls 0.468s = 25.4%
  run 4: admission at 2.280s; Journal.read 117 calls 0.667s = 29.3%
  (Journal.read_segments direct calls: 0; Journal.append calls: 0)

cold vs cached Journal.read() on the copy (3 runs): cold 176-181 ms, cached 0.44-0.47 ms per call

drain start, stack sampler (run 3 of 3; runs 1-2: reads 26.2%/27.2%, reads+folds 57.6%/55.7%):
  wall 1.933s
  journal-fold      0.592s  30.6%
  journal-read      0.486s  25.1%
  box-files         0.483s  25.0%
  other             0.145s   7.5%
  wait              0.101s   5.2%
  import            0.084s   4.3%
  git/subprocess    0.040s   2.1%
  => journal reads 25.1%; reads + folds 55.8%
  top fold sites: control.py:113(decisions) 0.091s, retro.py:308(emit_proposals) 0.060s,
    effects.py:18(__init__) 0.058s, caps.py:25(<genexpr>) 0.057s, caps.py:21(lineage) 0.057s,
    effects.py:49(_recorded) 0.044s, retro.py:396(__call__) 0.038s, caps.py:38(<genexpr>) 0.035s,
    storm.py:45(_history) 0.030s, storm.py:82(_evidence) 0.026s

status, stack sampler (run 3 of 3; runs 1-2: reads 52.1%/51.6%, reads+folds 61.3%/59.9%):
  wall 0.381s
  journal-read      0.195s  51.2%
  import            0.080s  21.1%
  journal-fold      0.035s   9.1%
  box-files         0.026s   6.8%
  other             0.021s   5.4%
  wait              0.016s   4.3%
  git/subprocess    0.008s   2.1%
  => journal reads 51.2%; reads + folds 60.3%
```
