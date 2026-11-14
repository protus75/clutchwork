# Review: snag

The diff covers most of the requested help surfaces, but the Help picker shows separator rows as selectable items, the Recent Steps Markdown tooltip runs its help lines together, and the lock icons no longer show who holds the lock.

## Findings

- [logic] vscode-chupa/extension.js:367 `chupa.help` passes `snap.helpPick` straight to `showQuickPick`. The snapshot marks separators as `{"kind": "separator", "label"}` (chupa/help.py:234), but VS Code only treats an item as a separator when `kind === vscode.QuickPickItemKind.Separator` (-1). So every topic kind ('view', 'command', 'verb', 'section', ...) shows up as an ordinary item the user can select. Selecting one has no `command` and no `topic`, so nothing happens. (do instead: When building the QuickPick list, map the closed snapshot value through a lookup table, e.g. `const KIND = { separator: vscode.QuickPickItemKind.Separator }` and `items.map(i => i.kind ? { ...i, kind: KIND[i.kind] } : i)`. Add `QuickPickItemKind` to a test mock only if a harness calls it.)
- [logic] vscode-chupa/extension.js:277 The Recent Steps tooltip passes `step.tooltip` (`date · stem · text\nwhat\nBefore: ...\nAfter: ...`) as raw Markdown into a `MarkdownString`. Markdown treats a single `\n` as a soft break, so the what/Before/After lines render as one run-on paragraph. Markdown characters in the step text, such as `_` in outcomes like `needs_human`, are also interpreted, and they are interpreted inside a string marked `isTrusted = true`. (do instead: Build it as `new vscode.MarkdownString().appendText(step.tooltip).appendMarkdown(`\n\n[Learn more](command:chupa.openHelp?...)`)`. `appendText` escapes the text and keeps its line breaks. Limit trust with `isTrusted = { enabledCommands: ['chupa.openHelp'] }`. Add the `appendText`/`appendMarkdown` members to the `MarkdownString` mock in tests/vscode_step_icons.js.)
- [logic] vscode-chupa/media/view.js:47 The lock and commit-lock titles used to show `snap.lock` / `snap.commitLock`, the lock holder. That was the only place the header showed who holds each lock. The diff replaces it with the help topic text, so hovering a 🔒 no longer tells the operator which process holds it. The ticket asks to add help to the lock icons, not to remove the holder information (same regression for `commitLock.title` at line 49). (do instead: Keep the holder and add the help, e.g. `lock.title = [snap.lock || 'unlocked', snap.help[snap.headerHelp.engine].text].join('\n')`, and do the same for `commitLock`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "5a714cae5bde16daf082c7491958d036cbcee627",
  "stem": "vscode-help-surfaces",
  "reviewed_sha": "5a714cae5bde16daf082c7491958d036cbcee627",
  "summary": "The diff covers most of the requested help surfaces, but the Help picker shows separator rows as selectable items, the Recent Steps Markdown tooltip runs its help lines together, and the lock icons no longer show who holds the lock.",
  "findings": [
    {
      "code": "logic",
      "path": "vscode-chupa/extension.js",
      "line": 367,
      "message": "`chupa.help` passes `snap.helpPick` straight to `showQuickPick`. The snapshot marks separators as `{\"kind\": \"separator\", \"label\"}` (chupa/help.py:234), but VS Code only treats an item as a separator when `kind === vscode.QuickPickItemKind.Separator` (-1). So every topic kind ('view', 'command', 'verb', 'section', ...) shows up as an ordinary item the user can select. Selecting one has no `command` and no `topic`, so nothing happens.",
      "paved_road": "When building the QuickPick list, map the closed snapshot value through a lookup table, e.g. `const KIND = { separator: vscode.QuickPickItemKind.Separator }` and `items.map(i => i.kind ? { ...i, kind: KIND[i.kind] } : i)`. Add `QuickPickItemKind` to a test mock only if a harness calls it.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "vscode-chupa/extension.js",
      "line": 277,
      "message": "The Recent Steps tooltip passes `step.tooltip` (`date · stem · text\\nwhat\\nBefore: ...\\nAfter: ...`) as raw Markdown into a `MarkdownString`. Markdown treats a single `\\n` as a soft break, so the what/Before/After lines render as one run-on paragraph. Markdown characters in the step text, such as `_` in outcomes like `needs_human`, are also interpreted, and they are interpreted inside a string marked `isTrusted = true`.",
      "paved_road": "Build it as `new vscode.MarkdownString().appendText(step.tooltip).appendMarkdown(`\\n\\n[Learn more](command:chupa.openHelp?...)`)`. `appendText` escapes the text and keeps its line breaks. Limit trust with `isTrusted = { enabledCommands: ['chupa.openHelp'] }`. Add the `appendText`/`appendMarkdown` members to the `MarkdownString` mock in tests/vscode_step_icons.js.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "vscode-chupa/media/view.js",
      "line": 47,
      "message": "The lock and commit-lock titles used to show `snap.lock` / `snap.commitLock`, the lock holder. That was the only place the header showed who holds each lock. The diff replaces it with the help topic text, so hovering a 🔒 no longer tells the operator which process holds it. The ticket asks to add help to the lock icons, not to remove the holder information (same regression for `commitLock.title` at line 49).",
      "paved_road": "Keep the holder and add the help, e.g. `lock.title = [snap.lock || 'unlocked', snap.help[snap.headerHelp.engine].text].join('\\n')`, and do the same for `commitLock`.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.5",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
