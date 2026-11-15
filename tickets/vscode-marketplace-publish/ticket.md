---
state: confirmed
source: human
priority: P3
kind: feature
---

## Depends on
- observe-verbs-host-extension
- pypi-package

## Context
- vscode-clutchwork/package.json
- vscode-clutchwork/extension.js
- dev.py
- docs/how-clutch-works.md
- docs/host-contract.md

## Goal / Why
Hosts get `vscode-clutchwork` only by building it from a clutch checkout with `./dev.py vscode`. It is to be published to the VS Code Marketplace under its existing proprietary license (`vscode-clutchwork/LICENSE`), so VS Code hosts install it from the Extensions view and receive updates (2026-11-06). Open VSX is out of scope. The extension stays a thin client over the installed `clutch` command (`observe-verbs-host-extension`); it never bundles the engine.

Three things are missing today:
- the manifest has no `repository` and no `extensionKind`;
- there is no listing README;
- there is no command that builds a release `.vsix`.

Without `extensionKind`, VS Code may run the extension on the UI side under WSL or Remote-SSH, away from the repo and the `clutch` command.

Publishing is a manual browser upload on the Marketplace management page, which signs in with the user's Microsoft account. Azure DevOps global PATs, which `vsce publish` uses from a local machine, retire on 2026-12-01 (VS Code publishing docs), so nothing here uses a token.

After this change, `./dev.py vscode-package` builds the current version's `.vsix` and prints where to upload it.

## Scope in / Scope out
- In: `vscode-clutchwork/package.json`:
  - `"extensionKind": ["workspace"]`;
  - `"repository": {"type": "git", "url": "https://github.com/protus75/clutchwork.git"}`;
  - `publisher` becomes `chunkydragon`, the registered Marketplace publisher ID (`clutch` was taken), so the extension ID becomes `chunkydragon.vscode-clutchwork`;
  - keep the `license` field and `vscode-clutchwork/LICENSE` unchanged;
  - a `"files": ["extension.js", "media/**", "README.md", "LICENSE"]` allowlist, so the VSIX packs nothing else (no `__pycache__` or engine code);
  - the `clutch.command` default becomes `["clutch"]`, the command `uv tool install clutch` puts on PATH. If `extension.js` repeats the default, it changes there too.
  - `extension.js`'s `clutch.openSettings` filter `@ext:clutch.vscode-clutchwork` becomes `@ext:chunkydragon.vscode-clutchwork`.
- In: `vscode-clutchwork/README.md`, the Marketplace listing page:
  - what the views show;
  - prerequisites: a repo with `tickets/`, and clutch installed (`uv tool install clutch`);
  - the `clutch.command` setting, with `["clutch"]` as the example for an installed engine;
  - that on WSL or Remote-SSH the extension runs on the remote side.
- In: a new `.vscode/settings.json` sets `"clutch.command": ["uv", "run", "clutch"]` for this repo, which runs the `clutch` console script that `uv sync` installs into `.venv`. This repo needs no wrapper script.
- In: `dev.py` gets a `vscode-package` subcommand.
  - It runs `npx --yes @vscode/vsce package --no-dependencies -o dist/vscode-clutchwork-<version>.vsix` (cwd `vscode-clutchwork/`, output path absolute under the repo root's `dist/`).
  - Then it prints that path and `https://marketplace.visualstudio.com/manage/publishers/chunkydragon`.
  - It packages the manifest's current version and never bumps it; the Marketplace refuses a version it already holds.
  - It installs nothing and publishes nothing.
  - The module docstring's usage lines and `--help` list it.
- In: `.gitignore` gains `dist/`.
- In: docs.
  - `docs/how-clutch-works.md` section 2.2: a `vscode-package` row, and how to release a version:
    - bump `version` in `vscode-clutchwork/package.json`;
    - run `./dev.py vscode-package`;
    - upload the printed `.vsix` on the `chunkydragon` management page: New extension the first time, the extension's Update action after that.
  - `docs/host-contract.md`: a host installs the extension from the Marketplace (Cursor and VSCodium: Install from VSIX), and installs clutch with `uv tool install clutch`. The VS Code extension paragraph's `clutch.command` default reads `["clutch"]`.
- Out:
  - the `./dev.py vscode` local install path;
  - the extension's views and commands;
  - `vsce publish`, tokens, and CI publishing;
  - git tags and pushes;
  - bundling Python or the engine into the VSIX;
  - Open VSX;
  - any change to `vscode-clutchwork/LICENSE`, the repo-root `LICENSE`, or the manifest `license` field.

## Scope fence
- vscode-clutchwork/package.json
- vscode-clutchwork/README.md
- vscode-clutchwork/extension.js
- .vscode/settings.json
- dev.py
- .gitignore
- docs/how-clutch-works.md
- docs/host-contract.md

## Acceptance criteria
1. `vscode-clutchwork/package.json` parses as JSON with `extensionKind == ["workspace"]`, a `repository.url` naming `github.com/protus75/clutchwork`, `publisher == "chunkydragon"`, `license == "SEE LICENSE IN LICENSE"`, `files == ["extension.js", "media/**", "README.md", "LICENSE"]`, and `clutch.command` defaulting to `["clutch"]`. `.vscode/settings.json` sets `clutch.command` to `["uv", "run", "clutch"]`. `vscode-clutchwork/README.md` and `vscode-clutchwork/LICENSE` exist. The first Verification command checks all of this.
2. `./dev.py --help` lists `vscode-package`, `dev.py` contains no `VSCE_PAT`, and `.gitignore` lists `dist/`. The second Verification command checks this.
3. `node --check vscode-clutchwork/extension.js` exits 0.
4. `docs/how-clutch-works.md` section 2.2 describes `vscode-package` and the upload steps, and `docs/host-contract.md` describes installing the extension.
5. `./dev.py test` exits 0.

## Verification
```
uv run python -c "import json, pathlib; p = json.load(open('vscode-clutchwork/package.json')); assert p['extensionKind'] == ['workspace'] and 'github.com/protus75/clutchwork' in p['repository']['url'] and p['publisher'] == 'chunkydragon' and p['license'] == 'SEE LICENSE IN LICENSE' and p['files'] == ['extension.js', 'media/**', 'README.md', 'LICENSE'] and p['contributes']['configuration']['properties']['clutch.command']['default'] == ['clutch']; assert json.load(open('.vscode/settings.json'))['clutch.command'] == ['uv', 'run', 'clutch']; assert pathlib.Path('vscode-clutchwork/README.md').is_file() and pathlib.Path('vscode-clutchwork/LICENSE').is_file()"
uv run python -c "import subprocess, pathlib; h = subprocess.run(['./dev.py', '--help'], capture_output=True, text=True, check=True).stdout; assert 'vscode-package' in h, h; s = pathlib.Path('dev.py').read_text(); assert 'VSCE_PAT' not in s; assert 'dist/' in pathlib.Path('.gitignore').read_text().split()"
node --check vscode-clutchwork/extension.js
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- anything uses a token or runs `vsce publish`;
- `vscode-package` bumps the version, installs, tags, or pushes;
- the VSIX bundles Python or engine code;
- a license file or the manifest `license` field changes or is removed, or anything publishes to Open VSX;
- `vscode-clutchwork/extension.js` changes beyond the `clutch.command` default and the `@ext:` settings filter.

## Time budget
- expected: 30m
- stuck: 90m
