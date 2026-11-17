---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: draft
---

## Depends on
none

## Context
- clutch/release.py
- clutch/roadmap.py::ship
- clutch/config.py::Release
- dev.py
- tests/unit/test_release_publish.py
- tests/unit/test_roadmap_ship.py
- clutch/docs/host-contract.md

## On-demand
- docs/how-clutch-works.md

## Goal / Why
When `ship` tags a release, each package command the host declares under `release.packages` runs after the tag, and every file it keeps is named in the ship digest lines. In this repo the declared command builds the VS Code package as `dist/vscode-clutchwork-<version>.vsix`. One file exists per version. A kept file is never overwritten, never committed (`dist/` is already in `.gitignore`), and never uploaded: Marketplace publishing stays the owner's manual step (roadmap decision 20). Today only `./dev.py vscode-package` builds the file, by hand, so the tags since 0.2.7 have none. The engine names no `./dev.py`: the host config carries the command.

## Scope in / Scope out
Scope in:
- `clutch/config.py`: a new `Package` model with `argv: Argv` and `kept: str`, a repo-relative glob such as `dist/vscode-clutchwork-*.vsix`. `Release` gains `packages: list[Package] = []`.
- `clutch/release.py`: a new `run_packages(repo, exec_, fs, env, config)` that returns digest lines. For each package it runs `argv` with `cwd=repo` and the env from `child_env`, so no provider key or token reaches it. The `kept` glob is matched against `fs.entries` of its parent directory. A nonzero exit yields the line `package: <argv[0]> failed (rc <n>)`. A run that leaves no match yields `package: nothing kept for <kept>`. Otherwise each match yields `package: kept <path>`. It never raises: the tag already exists, so a failed package must not hide the rest of the digest. This function takes `exec_` and `fs` as parameters, which is the seam through which a unit test runs it with fakes.
- `clutch/roadmap.py::ship`: after the tag and the optional publish, append the lines from `run_packages`. The only edit in `clutch/roadmap.py` is that call.
- `dev.py` `vscode-package`: when `dist/vscode-clutchwork-<version>.vsix` already exists, print that it is kept and return before touching any file, so a kept file is never overwritten. After packaging, restore the file that `vscode-package` rewrites with the `Built for` text to its prior text in a `finally`, so the `Built for` rewrite stays in the packaged file and the tracked tree stays clean for the next `publishable` check. The Marketplace upload line and the WSL path line stay as they are.
- `tests/integration/test_dev.py`: the one test that changes is `test_vscode_package_stamps_clutch_version`. It keeps its `packaged == [expected]` assertion and changes its final README assertion to equal the original fixture text, and its comment no longer says the stamped README must remain.
- `config.yaml`: declare `release: {packages: [{argv: [uv, run, python, dev.py, vscode-package], kept: dist/vscode-clutchwork-*.vsix}]}`.
- `clutch/docs/host-contract.md`: add `packages: []` to the `Release` defaults in the two `config-fields` rows that list them, and add a `Package` row with `required: [argv, kept]` and `defaults: {}`. Add a sentence saying `ship` runs each package after the tag and names the kept paths.
- `docs/how-clutch-works.md`: update the paragraph that describes `ship`'s release and publish steps, to add the package step. Also update the `vscode-package` row of the dev verbs table and the extension-release paragraph that tells the operator to run `./dev.py vscode-package` and then commit the README change. They say that the `Built for` stamp goes only into the packaged VSIX and the README is restored, that an existing `dist/vscode-clutchwork-<version>.vsix` is kept and not rebuilt, and drop the instruction to commit a README change. Change no other section.
- `tests/unit/test_release_publish.py`: the one existing expectation that may change is the `config.Release().model_dump()` equality, which gains `"packages": []`.
- `tests/unit/test_roadmap_ship.py`: the one change allowed is to give its fake `release` config `packages=[]`, so the new `ship` call reads an empty list.

Scope out: uploading anything, a `vsce publish` step, bumping the extension version, any change to `clutch publish`, and any new verb.

## Scope fence
- clutch/config.py
- clutch/release.py
- clutch/roadmap.py
- dev.py
- config.yaml
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_release_publish.py
- tests/unit/test_roadmap_ship.py
- tests/integration/test_dev.py
- tests/unit/test_release_packages.py
- tests/integration/test_dev_vscode_package_kept.py

## Acceptance criteria
1. `config.Release().model_dump()` equals `{"publish": False, "pypi_token": "UV_PUBLISH_TOKEN", "packages": []}`, not the two-key dict, checked in `tests/unit/test_release_publish.py`.
2. `run_packages` with a fake exec returning rc 0 and a fake fs listing `vscode-clutchwork-0.2.8.vsix` under `dist` returns `["package: kept dist/vscode-clutchwork-0.2.8.vsix"]`, not `[]`, checked in `tests/unit/test_release_packages.py`.
3. `run_packages` with a fake exec returning rc 1 returns a line starting `package: ` and containing `failed (rc 1)`, and does not raise, checked in `tests/unit/test_release_packages.py`.
4. `run_packages` with rc 0 and an empty fake directory returns `["package: nothing kept for dist/vscode-clutchwork-*.vsix"]`, not a `kept` line, checked in `tests/unit/test_release_packages.py`.
5. The env passed to the fake exec by `run_packages` has no provider auth variable and no `release.pypi_token` variable, checked in `tests/unit/test_release_packages.py`.
6. `run_packages` with `packages: []` returns `[]` and never calls exec, checked in `tests/unit/test_release_packages.py`.
7. After `dev.main()` runs `vscode-package` against a tmp root that already holds `dist/vscode-clutchwork-<version>.vsix`, the file's bytes are unchanged, and the packaging subprocess was not called, checked in `tests/integration/test_dev_vscode_package_kept.py`.
8. After a first `vscode-package` run against a tmp root with no kept file, the `.vsix` exists and the extension README under that tmp root equals its text from before the run, not the rewritten `Built for` text, checked in `tests/integration/test_dev_vscode_package_kept.py`.
9. `tests/integration/test_host_contract.py` passes with the `Package` row and the new `Release` default in the doc, and `tests/integration/test_roadmap_ship.py` and `tests/unit/test_roadmap_ship.py` still pass.
10. `config.yaml` loads through `config.load_config` and its `release.packages[0].kept` equals `dist/vscode-clutchwork-*.vsix`, checked in `tests/unit/test_release_packages.py` using the config text passed in by the test, not read from the repo.
11. `test_vscode_package_stamps_clutch_version` in `tests/integration/test_dev.py` passes with `packaged == [expected]` unchanged and the README equal to its original fixture text after the run, not the stamped text, checked by `./dev.py test tests/integration/test_dev.py`.

## Verification
```
./dev.py test tests/unit/test_release_packages.py tests/unit/test_release_publish.py tests/unit/test_roadmap_ship.py tests/integration/test_dev_vscode_package_kept.py tests/integration/test_dev.py tests/integration/test_host_contract.py tests/integration/test_roadmap_ship.py
```

## Definition of rejected
The branch is rejected if it uploads or publishes any file, commits a `.vsix`, overwrites a kept file, names `./dev.py` anywhere in `clutch/`, lets a failed package command raise out of `ship`, or leaves a tracked file dirty after `vscode-package`.

## Time budget
- expected: 30m
- stuck: 60m
