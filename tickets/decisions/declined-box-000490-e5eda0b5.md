---
id: declined-box-000490-e5eda0b5
kind: declined
link: box-000490-e5eda0b5
reopen_after_days: 30
---
The note asks to widen the engine-text scan in tests/integration/test_engine_text_verbs.py. Today it flags only 'dev.py'; it would also flag 'python -m clutch', so that an operator paved road cannot name module argv instead of a backticked clutch verb. It also asks for a decision on three remaining non-road mentions: the clutch/__main__.py module docstring, the argparse prog='python -m clutch' usage line, and a comment in clutch/observe.py.

This is a prevention check that only adds a test. It names no current harmful behavior. The seven operator roads it cites were removed by the merged ticket paved-roads-name-verbs: grep over clutch/ now finds 'python -m clutch' only in the __main__.py docstring, the argparse prog string, and an observe.py comment. tests/unit/test_paved_roads.py already pins the drain report heads and the Claude/Codex LOGIN_ROAD strings to `clutch drain` and asserts 'python -m clutch' is absent from the drain report. Of the three remaining hits, two are a docstring and a comment, which no operator sees as a road. The third, the argparse usage line, is cosmetic: `python -m clutch` still works in the venv where clutch is installed, so nothing an operator runs fails. Reopen if a new operator-facing paved road, refusal, or guide under clutch/ that names 'python -m clutch' instead of a `clutch <verb>' lands on main. Also reopen if a run or operator is shown to fail because they followed the 'python -m clutch' usage line from an installed (uv tool) clutch.

- grep 'python -m clutch' clutch/ on current main: only clutch/__main__.py:1 (module docstring), clutch/__main__.py:248 (argparse prog), clutch/observe.py:190 (docstring/comment)
- clutch/providers.py:485 and :535 LOGIN_ROAD now read 'run claude interactively and complete /login, then `clutch drain`' and 'run codex login, then `clutch drain`'
- tests/unit/test_paved_roads.py::test_drain_heads_name_the_drain_verb asserts 'python -m clutch' not in Report.render() text; test_login_roads_name_the_drain_verb pins both LOGIN_ROAD strings
- paved-roads-name-verbs is in the merged set
- tests/integration/test_engine_text_verbs.py::test_no_engine_text_names_dev_py scans clutch/ for 'dev.py' only, so the proposed change is test-only enforcement with no current violating road

Message: box-000490-e5eda0b5
