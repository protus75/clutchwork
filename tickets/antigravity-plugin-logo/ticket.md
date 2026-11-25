---
state: draft
source: human
priority: P2
kind: chore
---

## Depends on
- antigravity-plugin-bundle

## Context
- docs/antigravity-plan.md#6. Host and machine onboarding + publishable plugin bundle
- vscode-clutchwork/package.json

## Goal / Why
`host-antigravity-plugin` and `antigravity-plugin-bundle` ship the 24x24 monochrome `vscode-clutchwork/media/icon.svg` wireframe as `clutch/assets/logo.svg` and `assets/logo.svg`. That `stroke="currentColor"` SVG is designed for VS Code's Activity Bar, renders dark-on-dark inside `<img>` tags on dark themes, and reads as a generic flowchart rather than ClutchWork. A transparent 512x512 ClutchWork hatchling-and-gear PNG icon is already committed at `assets/hatchling-512.png` (with 10% margin baked in). Replacing the placeholder SVG logo with `logo.png` in the packaged wheel asset, committed Antigravity plugin bundle, `clutch/antigravity.py`, and `vscode-clutchwork/media/marketplace-icon.png` gives both Antigravity and the VS Code Marketplace the same crisp, theme-safe icon.

## Boundary contract
### Antigravity plugin logo asset and manifest
- disposition: replace
- owner: clutch/antigravity.py, clutch/assets/logo.png, assets/logo.png, plugin.json
- consumers: `clutch host antigravity`, Antigravity plugin loader, `agy plugin install`, `agy plugin validate --strict .`, `tests/unit/test_antigravity_plugin.py`, `tests/integration/test_antigravity_plugin.py`, `tests/unit/test_antigravity_bundle.py`, `tests/integration/test_antigravity_bundle.py`
- observable change: replace `clutch/assets/logo.svg` and `assets/logo.svg` with `clutch/assets/logo.png` and `assets/logo.png` copied byte-for-byte from `assets/hatchling-512.png`; update `DEFAULT_LOGO_PATH`, `plugin_manifest()["logo"]`, `install_plugin(...)`, and `portable_bundle_files(...)` in `clutch/antigravity.py` from `logo.svg` to `logo.png`; regenerate `plugin.json` with `"logo": "assets/logo.png"`.
- compatibility: `plugin.json` remains valid under Antigravity's documented `.png` logo format and exact nine top-level keys; no CLI flags or `mcp_config.json` / `skills/` files change. Old `clutch/assets/logo.svg` and `assets/logo.svg` are removed in the same change.
- acceptance: `clutch/assets/logo.png` and `assets/logo.png` match `assets/hatchling-512.png` byte-for-byte, `clutch/assets/logo.svg` and `assets/logo.svg` do not exist, and `plugin.json` plus `clutch/antigravity.py` reference `assets/logo.png`.
- tests: `tests/unit/test_antigravity_plugin.py`, `tests/integration/test_antigravity_plugin.py`, `tests/unit/test_antigravity_bundle.py`, `tests/integration/test_antigravity_bundle.py`
- post-merge source of truth: `clutch/antigravity.py`, `clutch/assets/logo.png`, `assets/logo.png`, `plugin.json`

### VS Code Marketplace icon
- disposition: replace
- owner: vscode-clutchwork/media/marketplace-icon.png
- consumers: `vscode-clutchwork/package.json` (`"icon": "media/marketplace-icon.png"`) and VSIX packaging
- observable change: replace `vscode-clutchwork/media/marketplace-icon.png` with the exact bytes of `assets/hatchling-512.png`.
- compatibility: path and PNG format referenced by `vscode-clutchwork/package.json` are unchanged; `vscode-clutchwork/media/icon.svg` (Activity Bar glyph) is untouched.
- acceptance: `vscode-clutchwork/media/marketplace-icon.png` matches `assets/hatchling-512.png` byte-for-byte.
- tests: `tests/integration/test_antigravity_bundle.py`
- post-merge source of truth: `vscode-clutchwork/media/marketplace-icon.png`

## Scope in / Scope out
Scope in:
- Copy `assets/hatchling-512.png` byte-for-byte to:
  - `clutch/assets/logo.png` (and delete `clutch/assets/logo.svg`)
  - `assets/logo.png` (and delete `assets/logo.svg`)
  - `vscode-clutchwork/media/marketplace-icon.png`
- In `clutch/antigravity.py`:
  - Update `DEFAULT_LOGO_PATH` from `Path(__file__).parent / "assets" / "logo.svg"` to `Path(__file__).parent / "assets" / "logo.png"`.
  - Update `plugin_manifest(...)` `"logo"` value from `"assets/logo.svg"` to `"assets/logo.png"`.
  - Update `install_plugin(...)` and `portable_bundle_files(...)` to write/map `"assets/logo.png"` instead of `"assets/logo.svg"`.
- Regenerate `plugin.json` from `clutch.antigravity.portable_bundle_files(...)` so `"logo"` is `"assets/logo.png"` and all other fields remain identical.
- Update the logo-path expectations in the four tests created by `host-antigravity-plugin` and `antigravity-plugin-bundle`:
  - `tests/unit/test_antigravity_plugin.py`: update `assets/logo.svg` expectations to `assets/logo.png`.
  - `tests/integration/test_antigravity_plugin.py`: update the logo check to verify `clutch/assets/logo.png` exists, matches `assets/hatchling-512.png` byte-for-byte (and `clutch/assets/logo.svg` does not exist), and loads via `install_plugin(..., logo_bytes=None)` into a `FakeFileSystem`.
  - `tests/unit/test_antigravity_bundle.py`: update `assets/logo.svg` expectations in `plugin_manifest` and `portable_bundle_files` tests to `assets/logo.png`.
  - `tests/integration/test_antigravity_bundle.py`: update the drift check to read `clutch/assets/logo.png`, verify `assets/logo.png` matches `portable_bundle_files(...)` byte-for-byte, verify `assets/logo.svg` does not exist, and verify `vscode-clutchwork/media/marketplace-icon.png` matches `assets/hatchling-512.png` byte-for-byte.

Scope out:
- Do not modify `vscode-clutchwork/media/icon.svg`, `vscode-clutchwork/package.json`, `mcp_config.json`, `skills/`, `clutch/__main__.py`, `clutch/doctor.py`, any documentation or conduct files, or any of the 18 source files under `assets/{badge,hatchling,medallion}-*`.

## Scope fence
- clutch/antigravity.py
- clutch/assets/logo.png
- clutch/assets/logo.svg
- assets/logo.png
- assets/logo.svg
- plugin.json
- vscode-clutchwork/media/marketplace-icon.png
- tests/unit/test_antigravity_plugin.py
- tests/integration/test_antigravity_plugin.py
- tests/unit/test_antigravity_bundle.py
- tests/integration/test_antigravity_bundle.py

## Acceptance criteria
1. `clutch.antigravity.plugin_manifest(...)` sets `"logo": "assets/logo.png"` (not `"assets/logo.svg"`), `install_plugin(...)` writes `assets/logo.png`, `portable_bundle_files(...)` maps `"assets/logo.png"`, and `clutch/antigravity.py` retains >= 90% unit branch coverage; verified by `./dev.py test tests/unit/test_antigravity_plugin.py tests/unit/test_antigravity_bundle.py`.
2. `clutch/assets/logo.png`, `assets/logo.png`, and `vscode-clutchwork/media/marketplace-icon.png` each exist and match `assets/hatchling-512.png` byte-for-byte, `clutch/assets/logo.svg` and `assets/logo.svg` do not exist, and `plugin.json` plus all other root bundle files match `portable_bundle_files(...)` byte-for-byte; verified by `./dev.py test tests/integration/test_antigravity_plugin.py tests/integration/test_antigravity_bundle.py`.

## Verification
```
./dev.py test tests/unit/test_antigravity_plugin.py tests/unit/test_antigravity_bundle.py tests/integration/test_antigravity_plugin.py tests/integration/test_antigravity_bundle.py
```

## Definition of rejected
`clutch/assets/logo.svg` or `assets/logo.svg` remains in the repository, any of `clutch/assets/logo.png`, `assets/logo.png`, or `vscode-clutchwork/media/marketplace-icon.png` differs from `assets/hatchling-512.png`, `vscode-clutchwork/media/icon.svg` is modified, or `clutch/antigravity.py` drops below 90% unit coverage.

## Time budget
- expected: 10m
- stuck: 20m
