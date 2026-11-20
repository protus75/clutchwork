---
facet: theme/light
version: "0.1"
summary: Use dark text and clearly distinguishable links on light surfaces.
aliases: []
applies_to: [render]
requires: [{format: [html, pdf]}]
---
<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: light
relates: []
owner: engine
verified: d7719818
hash: a17bbac7c359757b85da97a14ccd881030cd504f62948eb33a89617f8977715c
-->

Apply the paired light.css tokens to HTML and its PDF render. Use the page surface for prose, the secondary surface for code or table headers, and the border token for boundaries. Keep links underlined and statuses labeled in text so color is supplementary.
