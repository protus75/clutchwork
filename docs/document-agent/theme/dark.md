---
facet: theme/dark
version: "0.1"
summary: Use light text and clearly distinguishable links on dark surfaces.
aliases: []
applies_to: [render]
requires: [{format: [html, pdf]}]
---
<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: dark
relates: []
owner: engine
verified: d7719818
hash: bda607a851c119c0c2778ccb77ac0bdaf53b4c2faf58efa481235923e3a970fd
-->

Apply the paired dark.css tokens to HTML and its PDF render. Use the same semantic roles as the light theme so changing theme preserves hierarchy and reading order. Pair foreground and background explicitly in code and tables. Keep links underlined and statuses labeled in text so color is supplementary.
