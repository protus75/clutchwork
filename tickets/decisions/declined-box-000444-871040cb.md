---
id: declined-box-000444-871040cb
kind: declined
link: box-000444-871040cb
reopen_after_days: 14
---
When nothing is selected, the Details view in the VS Code extension shows a fixed sentence written into media/detail.js, not the `view.chupa.details` help topic. The rejected umbrella ticket vscode-help asked for the topic text there. Its split ticket vscode-help-surfaces left this out on purpose, because the snapshot has no key that names a topic for the empty state and the thin-wrapper rule forbids JavaScript from hard-coding one. The suggestion is to add a snapshot field that carries that key once vscode-help-registry merges, so detail.js can show the topic text.

This does not describe incorrect runtime behavior. The empty Details view already shows an explanatory sentence, and the request is to swap it for registry help text, which is a help-coverage improvement. It also depends on vscode-help-registry, which has not merged, so the snapshot field it would add has nothing to read yet. vscode-help-surfaces records the omission as a deliberate scope choice (ticket.md line 62), not as a defect. Reopen if, after vscode-help-registry and vscode-help-surfaces merge, an operator shows that the empty Details view misleads or strands them, or that the fixed sentence has drifted from the `view.chupa.details` topic.

- tickets/vscode-help-surfaces/ticket.md:62: 'The Details view's empty-state sentence stays as it is: the snapshot names no topic key for the empty state, and JavaScript may not hard-code one.'
- tickets/vscode-help/ticket.md:173 (state: rejected umbrella) asked that 'the empty state shows the `view.chupa.details` topic `text`, not the hard-coded sentence.'
- tickets/vscode-help-registry/ticket.md:58 defines a `view.chupa.details` topic, but that ticket is still open, not merged.
- The current empty state already shows a hard-coded explanatory sentence, so no help is missing outright and nothing behaves incorrectly.

Message: box-000444-871040cb
