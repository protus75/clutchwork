---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- vscode-clutchwork/extension.js
- vscode-clutchwork/README.md
- tests/vscode_task_identity.js
- tests/regress_vscode_task_identity.py

## Goal / Why
When the `clutch.command` binary does not exist (no `uv sync` yet, a native Windows venv layout, a typo in the setting), node's `execFile` fails with `err.code === 'ENOENT'` and the message `spawn .venv/bin/clutch ENOENT`. The extension shows that raw text in the views (snapshot error) and in error toasts (`order`, `prompt`, box prompt). It does not say that the `clutch.command` setting is the fix.

After this change, every `runData` failure with `err.code === 'ENOENT'` reports `clutch command not found: <binary> (run from <root>). Set clutch.command in settings.`, where `<binary>` is the first element of `clutch.command` and `<root>` the workspace root. Other failures keep their current text.

## Scope in / Scope out
- In: `vscode-clutchwork/extension.js` `runData`: when the `execFile` callback's error has `code === 'ENOENT'`, pass the callback an error whose `message` is the text above, and empty `stderr`, so the existing `(stderr || err.message)` call sites show it unchanged. This maps a closed Node error code to a message; it is not a policy choice and needs no snapshot field.
- In: new `tests/vscode_command_not_found.js` harness in the style of `tests/vscode_task_identity.js` (stub `vscode` module, real `child_process`). Usage: `node tests/vscode_command_not_found.js <root> <binary>`. It uses `<root>` as `workspaceFolders[0]` and returns `[<binary>]` for `clutch.command`. It activates the extension, captures the provider passed to `registerWebviewViewProvider('clutch.tickets', ...)`, and calls `resolveWebviewView` with a stub view. The stub's `webview` supplies `cspSource`, `asWebviewUri`, `options`, an `onDidReceiveMessage` whose handler the harness keeps, and a `postMessage` that records messages; the stub `vscode.Uri` adds `joinPath`. The harness then sends that handler `{type: 'ready'}`, which triggers a snapshot refresh. When `postMessage` receives `{type: 'error', message}`, it prints `JSON.stringify(message)` and exits 0. `extension.js` exports stay unchanged.
- In: new `tests/integration/test_vscode_command_not_found.py`. Each test creates `tmp_path / "tickets"` (so `clutchRoot()` picks `tmp_path`), runs `node tests/vscode_command_not_found.js <tmp_path> <binary>` with `subprocess.run` (argv list, `check=True`, a timeout), and parses stdout as JSON.
- In: `vscode-clutchwork/README.md`: one sentence saying a missing command shows a `clutch command not found` message naming the `clutch.command` setting.
- Out:
  - `ProcessExecution` tasks (`devCommand`); VS Code's task terminal already reports a missing executable;
  - `vscode-clutchwork/package.json` and the `clutch.command` default (`vscode-venv-default`);
  - other error codes, retries, or auto-detecting an interpreter;
  - engine code under `clutch/`.

## Scope fence
- vscode-clutchwork/extension.js
- vscode-clutchwork/README.md
- tests/vscode_command_not_found.js
- tests/integration/test_vscode_command_not_found.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_vscode_command_not_found.py` passes. Its test with binary `.venv/bin/clutch-missing` asserts the printed error equals `clutch command not found: .venv/bin/clutch-missing (run from <tmp>). Set clutch.command in settings.` with `str(tmp_path)` in place of `<tmp>`. That rules out the raw `spawn .venv/bin/clutch-missing ENOENT` text and a message that omits the binary or the setting name.
2. The same file has a second test with binary `false` (exists, exits 1, no stderr) that asserts the printed error does not contain `clutch command not found`, so non-ENOENT failures keep their existing text.
3. `node tests/vscode_task_identity.js` still prints three task definitions (the harness is unchanged and `extension.js` still activates under it).
4. `vscode-clutchwork/README.md` contains `clutch command not found` and `clutch.command`.
5. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_vscode_command_not_found.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- the extension checks for the file with `fs.existsSync` or similar before spawning, instead of reading the spawn error;
- the message suggests a specific path or interpreter, or the extension changes `clutch.command` itself;
- any call site other than `runData` changes how it formats errors;
- `vscode-clutchwork/package.json` changes.

## Time budget
- expected: 25m
- stuck: 75m
