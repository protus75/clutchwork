---
facet: type/release-notes
version: "0.1"
summary: Explain what changed in a release, who is affected, and what action they need to take.
aliases: []
applies_to: [create, derive]
requires: []
---

Write release notes for the selected audience using the supplied local release evidence. Establish which changes belong to the release before writing. Use the changelog and merged work within the release range to find candidates. Check the resulting behavior against its owning help, contract, or implementation. A roadmap entry or ticket goal alone cannot establish delivery.

## Release identity

Lead with the product and version. Include the date and availability when the evidence establishes them. In Clutch, a local release tag records the version and commit. A claim that users can download a published package needs evidence of publication. If the sources describe intended work only, label the notes as a draft and identify what still needs confirmation.

## Changes and fixes

Lead with the changes that affect the reader most. For each, name the affected user or integration and describe the observable difference from the preceding release. For a fix, give the triggering condition and corrected result. Group tickets that delivered one change into one entry. Keep a source reference for each substantive claim. An empty changelog heading leaves the contents unknown.

## Upgrade actions

Put required action first when existing workflows will break. Give the affected versions or consumers, the old and replacement behavior, when to migrate, and how to verify success. Use exact command or configuration spelling from the supplied owning artifact. Include compatibility or rollback guidance only when documented.

## Known issues

Include outstanding limitations that apply to this release, their observable symptoms, and any verified workaround. Omit empty sections. Before returning the notes, check each version, command, date, and availability claim against the release evidence. On derivation, identify the canonical sections used for the enclosing surface.
