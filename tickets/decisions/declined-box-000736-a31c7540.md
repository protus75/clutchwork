---
id: declined-box-000736-a31c7540
kind: declined
link: box-000736-a31c7540
reopen_after_days: 30
---
The task-identity regression reproducer (tests/regress_vscode_task_identity.py and its node harness tests/vscode_task_identity.js) is not run by any test suite or Check. When cli-group-view changed the snapshot bootstrap argv to ['view', 'snapshot'], the stale harness was found only by running it by hand. The note proposes running it from a node-gated integration test or folding it into tests/integration/test_extension_argv.py.

This proposal only adds test coverage. It shows no current, reachable incorrect runtime behavior. The harness was already updated during cli-group-view: tests/vscode_task_identity.js line 34 now answers 'view snapshot'. The extension's Stop/Kill task-identity fix (merged vscode-task-identity) is not reported broken. A stale reproducer that nothing runs does not make the extension or engine misbehave. Reopen if an extension.js change ships a task-identity regression, such as Stop/Kill starting no task or a duplicate task definition, that a suite-run reproducer would have caught.

- tests/vscode_task_identity.js:34 already matches args 'view snapshot', so the harness is current on main
- Grep finds tests/regress_vscode_task_identity.py referenced only by docs/roadmap.md:135 and no test module, which confirms it is not run by any suite
- tests/integration/test_regress_scripts_guarded.py globs regress_*.py only to check the import guard, not to run the reproducers
- The vscode-task-identity fix is merged, and no report shows Stop/Kill broken again

Message: box-000736-a31c7540
