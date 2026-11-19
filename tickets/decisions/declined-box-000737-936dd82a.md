---
id: declined-box-000737-936dd82a
kind: declined
link: box-000737-936dd82a
reopen_after_days: 30
---
The message proposes one unit test that parses every argv the snapshot sends to the VS Code extension. Today only the `commands` table from `extension_fields()` is checked against `_parser()`. The other three tables are not checked: `engineVerbs[*].argv`, `drainCommand` and `verdictCommands`. If a command is renamed, a picker action could keep running the old name while every test still passes.

This only adds test coverage. No command in the snapshot is broken today. In current `clutch/observe.py` (lines 900-913), every argv uses the grouped command tree: `engine drain --detach`, `engine serve`, `engine stop`, `engine kill`, `view status`, `engine retro` and `ticket confirm|reject --extension`. The stale `['status']` entry the message saw at 09082c68 has already been fixed, so no picker action runs a removed command now. A test that guards against a future rename is speculative hardening, and that is declined here. Reopen if a snapshot argv in `engineVerbs`, `drainCommand` or `verdictCommands` fails to parse with `clutch.__main__._parser()` on main, or if an extension action runs a removed command.

- clutch/observe.py:900 drainCommand = ['engine', 'drain', '--detach']
- clutch/observe.py:901-908 engineVerbs argv all grouped (Status is ['view', 'status'])
- clutch/observe.py:913 verdictCommands = ['ticket', verb, '--extension']
- tests/unit/test_observe_extension_fields.py:27-31 parse-checks only extension_fields()['commands']

Message: box-000737-936dd82a
