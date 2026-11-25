---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
none

## Context
- docs/antigravity-plan.md#4. Antigravity MCP App dashboard replacing VS Code views
- docs/antigravity-plan.md#Open decisions
- dev.py
- package.json
- .gitignore
- vscode-clutchwork/media/view.css
- vscode-clutchwork/media/ticket-lifecycle.svg
- tests/unit/test_dev_testguard.py

## On-demand
- docs/how-clutch-works.md
- CLAUDE.md
- AGENTS.md

## Goal / Why
Roadmap row 223 (`mcp-app-dashboard`, `docs/antigravity-plan.md` §4, Open decisions #1), part 2 of 3. Antigravity renders an MCP App as one self-contained HTML document under a default CSP of `default-src 'none'`, and nothing in this repo builds one.

After this ticket, `./dev.py ui-bundle` builds a single self-contained `clutch/ui/dashboard.html` (gitignored build artifact) from a minimal `clutch/ui/app.js` boot module and `clutch/ui/dashboard.css`, inlining `vscode-clutchwork/media/view.css`, `vscode-clutchwork/media/ticket-lifecycle.svg`, and the esbuild-bundled JS including `@modelcontextprotocol/ext-apps`. The minimal app connects through `App`, applies `applyDocumentTheme` and `applyHostStyleVariables`, and exposes `ClutchDashboardApp.createDashboardApp`; the six dashboard surfaces are `mcp-dashboard-surfaces`. `CLAUDE.md` and `AGENTS.md` extend the Pure Python operator-only client JS exception to `clutch/ui/`, and `CLAUDE.md`'s Command surface rule and `docs/how-clutch-works.md` §2.2 list `ui-bundle`, in the same change that adds the JS and the task.

Rejected simpler approach: hand-writing a raw `postMessage` bridge with no bundler. That skips the SEP-1865 handshake, auto-resize, and host-context contract owned by `@modelcontextprotocol/ext-apps`, and committing a prebuilt ~300 KB HTML file would blow the Review prompt render bound.

## Boundary contract

### Self-contained MCP App dashboard bundle
- disposition: create
- owner: clutch/ui/app.js
- closest existing: `vscode-clutchwork/extension.js` (VS Code webview host) and `vscode-clutchwork/media/` (shared DOM and SVG renderers)
- earning reason: an MCP App iframe under Antigravity's `default-src 'none'` CSP needs one self-contained HTML document speaking the `@modelcontextprotocol/ext-apps` transport; `vscode-clutchwork/extension.js` depends on the `vscode` API and cannot run in that iframe.
- consumers: `clutch/mcp.py` (`resources/read`), Antigravity side pane and sidebar, `mcp-dashboard-surfaces`
- observable change: adds `clutch/ui/app.js` (exports `createDashboardApp(options)`, registers `ontoolinput`, `ontoolresult`, and `onhostcontextchanged` before `connect()`, applies `applyDocumentTheme` and `applyHostStyleVariables` after `connect()` and on every host context change, and auto-boots only when `document` exists and `__CLUTCH_DASHBOARD_NO_AUTOBOOT__` is unset) and `clutch/ui/dashboard.css`; `clutch/ui/dashboard.html` is a gitignored build output.
- compatibility: `vscode-clutchwork/` files and tests are untouched.
- acceptance: criteria 1 and 3
- tests: tests/unit/test_dev_ui_bundle.py
- post-merge source of truth: clutch/ui/app.js

### Repo UI bundle build task
- disposition: extend
- owner: dev.py
- consumers: developers, `clutch/ui/dashboard.html`, `tests/unit/test_dev_ui_bundle.py`, `mcp-dashboard-surfaces`
- observable change: adds `build_ui_bundle(root=ROOT, out=None, run_cmd=subprocess.run) -> Path` (default `out` is `root / 'clutch/ui/dashboard.html'`) and the `ui-bundle` subcommand, which runs local esbuild with `--bundle --format=iife --platform=browser --global-name=ClutchDashboardApp --minify` on `clutch/ui/app.js`, inlines `vscode-clutchwork/media/view.css`, `clutch/ui/dashboard.css`, `vscode-clutchwork/media/ticket-lifecycle.svg`, and the bundled JS (escaping `</script` as `<\/script`) into `out`, and exits non-zero with a clear message when esbuild or a source asset is missing.
- compatibility: existing `./dev.py` tasks (`test`, `visual-baseline`, `vscode`, `vscode-package`) keep their exact behavior.
- acceptance: criteria 1 and 3
- tests: tests/unit/test_dev_ui_bundle.py, tests/unit/test_dev_testguard.py
- post-merge source of truth: dev.py

### Repo rules and build-task docs
- disposition: extend
- owner: CLAUDE.md
- consumers: agents working in this repo, `AGENTS.md`, `docs/how-clutch-works.md` readers
- observable change: the Pure Python rule's operator-only client JS exception in both `CLAUDE.md` and `AGENTS.md` (outside the managed block; repo-rule home) names `clutch/ui/` alongside `vscode-clutchwork/`; the Command surface rule in `CLAUDE.md` (repo-rule home; `AGENTS.md` does not carry it) lists `ui-bundle`; `docs/how-clutch-works.md` §2.2 gains a `ui-bundle` row.
- compatibility: the managed block and `clutch/hostfiles.py` `CORE_TEMPLATE` are untouched.
- acceptance: criterion 2
- tests: tests/integration/test_help.py
- post-merge source of truth: CLAUDE.md

## Scope in / Scope out
In:
- `package.json` and `pnpm-lock.yaml`: add `@modelcontextprotocol/ext-apps`, `esbuild`, and `zod` to `devDependencies` (via `pnpm add -D`).
- `.gitignore`: ignore `clutch/ui/dashboard.html`.
- `dev.py`: `build_ui_bundle` and the `ui-bundle` subcommand as declared in the boundary contract, listed in the module docstring and argparse subparsers.
- `clutch/ui/app.js`: imports `App`, `applyDocumentTheme`, `applyHostStyleVariables` from `@modelcontextprotocol/ext-apps`; exports pure `createDashboardApp(options)` (exposed as `ClutchDashboardApp.createDashboardApp`) that builds the `App`, registers handlers before `await app.connect()`, and applies theme tokens after connect and on `onhostcontextchanged`; guards auto-boot with `typeof document !== "undefined" && !globalThis.__CLUTCH_DASHBOARD_NO_AUTOBOOT__`.
- `clutch/ui/dashboard.css`: base layout using `--color-background-*`, `--color-text-*`, `--color-border-*`, and `--font-sans` with fallbacks.
- `CLAUDE.md`, `AGENTS.md`, `docs/how-clutch-works.md`: the rule and §2.2 updates declared in the boundary contract.
- New `tests/unit/test_dev_ui_bundle.py` (`tmp_path` and a fake `run_cmd` only; no real esbuild, no repo file reads): writes stub sources under `tmp_path`, asserts the output inlines both CSS files, the SVG, and the JS, escapes a raw `</script>` in the JS, invokes esbuild with the declared flags, and refuses (non-zero / raised error, no output written) when a source asset is missing.
- Engine-written `# clutch:meta` headers on newly created Python test files under `tests/` updated by Check.

Out:
- Committing `clutch/ui/dashboard.html` or packaging it into wheels.
- The six dashboard surfaces, host adapter, shared renderer imports, Node harness, and integration test (`mcp-dashboard-surfaces`).
- `clutch/mcp.py` and its tests (`mcp-dashboard-resource`).
- `vscode-clutchwork/`, `clutch/help.py`, `clutch/hostfiles.py`.
- Tests in any of the seven hot test files.

## Scope fence
- dev.py
- package.json
- pnpm-lock.yaml
- .gitignore
- clutch/ui/
- CLAUDE.md
- AGENTS.md
- docs/how-clutch-works.md
- tests/unit/test_dev_ui_bundle.py

## Acceptance criteria
1. `tests/unit/test_dev_ui_bundle.py` checks `dev.build_ui_bundle` with `tmp_path` and a fake `run_cmd` writes one HTML file inlining both CSS files, the SVG, and the bundled JS with `</script` escaped, passes `--bundle --format=iife --platform=browser --global-name=ClutchDashboardApp --minify` to esbuild, and refuses without writing output when a source asset is missing. Verified by `./dev.py test tests/unit/test_dev_ui_bundle.py tests/unit/test_dev_testguard.py`.
2. `CLAUDE.md` and `AGENTS.md` both name `clutch/ui/` in the Pure Python exception, `CLAUDE.md`'s Command surface rule lists `ui-bundle`, and `docs/how-clutch-works.md` §2.2 has a `ui-bundle` row; help and doc-link tests pass with `./dev.py test tests/integration/test_help.py tests/unit/test_main_help.py`.
3. Existing `./dev.py` tasks and shared-renderer tests pass unchanged. Verified by `./dev.py test tests/unit/test_dev_testguard.py tests/integration/test_ui_shared_renderers.py`.

## Verification
```
./dev.py test tests/unit/test_dev_ui_bundle.py tests/unit/test_dev_testguard.py tests/unit/test_main_help.py tests/integration/test_help.py tests/integration/test_ui_shared_renderers.py
```

## Definition of rejected
- The built HTML loads external scripts or stylesheets, or the app hand-rolls `postMessage` instead of `@modelcontextprotocol/ext-apps`.
- `clutch/ui/dashboard.html` is committed, or a missing source silently writes broken HTML.
- `CLAUDE.md` and `AGENTS.md` disagree on the Pure Python exception, or the managed block is edited.
- Any file outside `## Scope fence` is modified.

## Time budget
- expected: 15m
- stuck: 30m