---
facet: format/markdown
version: "0.1"
summary: Return the authored Markdown as the render artifact.
aliases: []
applies_to: [render]
requires: []
---

Use the selected document revision as the artifact. Preserve its text, heading anchors, relative link destinations, tables, fenced code, extraction markers, and whitespace inside protected regions. Mermaid stays in its original fenced block.

Rendering Markdown takes no theme. A useful check is a byte comparison against the input revision. A render must not rewrite the canonical source or ask a model to restyle it.
