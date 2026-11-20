---
facet: format/html
version: "0.1"
summary: Render Markdown to a single HTML document with embedded theme CSS.
aliases: []
applies_to: [render]
requires: []
---
<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: html
relates: []
owner: engine
verified: d7719818
hash: 2718cd4a44182a8940598a78a65e36a3b078599eeef0b88b978b45c54abe9f51
-->

Use the planned Markdown renderer with tables, footnotes, and heading anchors enabled. Preserve heading order, internal link targets, list nesting, table structure, and code content. Render Mermaid as fenced code. Embed the shared stylesheet and the selected theme tokens in the document so theme styling needs no external asset.

Check with a document containing a heading link, footnote, table, and code fence. The link should reach its heading, the footnote should resolve, and the code should display literally. Changing theme changes presentation while preserving the document text and structure.
