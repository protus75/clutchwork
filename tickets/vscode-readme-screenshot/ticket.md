---
state: confirmed
source: human
priority: P0
kind: chore
---

## Depends on
- none

## Context
- vscode-clutchwork/README.md
- vscode-clutchwork/package.json
- vscode-clutchwork/media/ticket-lifecycle.svg

## Goal / Why
The Marketplace listing renders `vscode-clutchwork/README.md`, and today it has no picture of the extension, so a visitor cannot see what the views look like before installing. After this change, the README shows the screenshot `vscode-clutchwork/images/ClutchExt.png` (Details, Recent Steps, and Tickets views with the ticket context menu open) and the ticket lifecycle diagram `vscode-clutchwork/images/Lifecycle.png` (a PNG export of `vscode-clutchwork/media/ticket-lifecycle.svg`), so both are visible on the listing page.

## Scope in / Scope out
- In: add one markdown image line to `vscode-clutchwork/README.md`, directly after the first paragraph under `# clutch tickets` and before the `Built for` line, separated by blank lines:
  `![clutch tickets views in VS Code](https://github.com/protus75/clutchwork/raw/HEAD/vscode-clutchwork/images/ClutchExt.png)`
  Directly below it, separated by a blank line, a second image line:
  `![clutch ticket lifecycle](https://github.com/protus75/clutchwork/raw/HEAD/vscode-clutchwork/images/Lifecycle.png)`
  The diagram is embedded as the PNG, never the SVG, because vsce rejects SVG images in a README.
  Both targets are absolute `https://` URLs because the extension lives in a repo subfolder and vsce may rewrite a relative image path against the repo root.
- Out: the image files themselves, `vscode-clutchwork/media/ticket-lifecycle.svg`, `vscode-clutchwork/package.json` (`files` already excludes `images/`, so the PNG stays out of the VSIX), a Marketplace `icon`, `galleryBanner`, and `dev.py`.

## Scope fence
- vscode-clutchwork/README.md

## Acceptance criteria
1. `vscode-clutchwork/README.md` contains exactly two images, the two lines exactly as given in Scope in, placed after the first paragraph and before the `Built for` line.
2. The `Built for [clutch X](https://pypi.org/project/clutchwork/X/).` line is unchanged and still occurs exactly once, so `./dev.py vscode-package` can still stamp it.
3. `./dev.py test` exits 0.

## Verification
```
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- any file other than `vscode-clutchwork/README.md` changes;
- either image target is a relative path;
- any image target ends in `.svg`;
- the `Built for` line changes or is duplicated.

## Time budget
- expected: 5m
- stuck: 20m
