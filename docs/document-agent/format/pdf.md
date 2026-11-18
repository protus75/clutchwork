---
facet: format/pdf
version: "0.1"
summary: Render the themed HTML through the host-configured PDF command.
aliases: []
applies_to: [render]
requires: []
---

Use the same document revision and themed HTML as the HTML format. Pass that HTML through the host’s documents.render.pdf argv using the exec seam and the host-command lock when available. Preserve the order of headings, body text, tables, and code across page breaks.

If no PDF command is configured, report the missing documents.render.pdf setting. Report conversion failures through the render operation. A successful render produces a readable PDF containing the source material, including text at the end of a multi-page table or code block.
