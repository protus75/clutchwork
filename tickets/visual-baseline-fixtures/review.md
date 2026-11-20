# Review: snag

The test and report match the format, but the six generate cases are byte-for-byte copies of two image sets (case-20 also reuses case-13's candidate), so criterion 3 and the goal of varied good and broken placements are met only by duplication, and the copies skew the committed agreement measurement.

## Findings

- [acceptance] eval/visual/case-03/case.json:4 case-03 is an exact copy of case-01: same case.json blob 65850ced, same input.png 9d8ee104, same base.png 0c9ceda0 and same candidate.png 5e3cad69. It adds no new generate case. It only repeats one measurement in the report. (do instead: Replace case-03 with a new generate case that has its own input, base, candidate and requested position and scale (a good placement, or a different break such as clipped, duplicated, seams or wrong scale), then label it with `uv run python -m eval.visual_harness label`.)
- [acceptance] eval/visual/case-04/case.json:4 case-04 is an exact copy of case-02: same case.json blob 65850ced, same input and base images, and same candidate.png b60324fe. Criterion 3 needs at least 6 generate cases, and copies only meet it on paper. (do instead: Redraw case-04 as a separate generate case with its own composite and criterion, then relabel it through the panel.)
- [acceptance] eval/visual/case-06/case.json:4 case-06 is a third exact copy of case-02: same case.json blob 65850ced, same input and base images, and same candidate.png b60324fe. The six generate cases contain only two distinct image sets. (do instead: Redraw case-06 as a separate generate case, so the set holds at least 6 different generate cases that include good placements and different kinds of break.)
- [acceptance] eval/visual/case-05/case.json:4 case-05 uses the same images and the same criterion as case-01 and case-03 (candidate 5e3cad69), but its label is `accept` while theirs are `reject`. Identical inputs carry opposite ground truth, so none of the generate cases is a clearly good placement, which the ticket's 'good and the broken placements' asks for. (do instead: Draw a candidate whose placement plainly meets its stated position and scale, so the good case differs visibly from the broken ones, and let the panel label it. Do not keep identical cases that carry opposite labels.)
- [acceptance] eval/visual/case-20/case.json:4 case-20's candidate.png (6732d350) is the same file as case-13's, and its criterion only rewords case-13's. It adds no new image to the 20-case minimum and repeats one measurement in the report. (do instead: Replace case-20 with a new candidate image, for example a missing element, an off-position shape or a clipped object, label it through the panel, and rerun `./dev.py visual-baseline` so the report covers the corrected set.)
- [acceptance] eval/visual_report.json:2 The report's 20 cases include the duplicate cases listed above, so its overall and per-row agreement do not measure 20 distinct cases. (do instead: After the duplicates are replaced and labelled, run `./dev.py visual-baseline` once over the final set and commit the regenerated report.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "5fa819ff660305d03f8afe4d6980b43bc5e920b7",
  "stem": "visual-baseline-fixtures",
  "reviewed_sha": "5fa819ff660305d03f8afe4d6980b43bc5e920b7",
  "summary": "The test and report match the format, but the six generate cases are byte-for-byte copies of two image sets (case-20 also reuses case-13's candidate), so criterion 3 and the goal of varied good and broken placements are met only by duplication, and the copies skew the committed agreement measurement.",
  "findings": [
    {
      "code": "acceptance",
      "path": "eval/visual/case-03/case.json",
      "line": 4,
      "message": "case-03 is an exact copy of case-01: same case.json blob 65850ced, same input.png 9d8ee104, same base.png 0c9ceda0 and same candidate.png 5e3cad69. It adds no new generate case. It only repeats one measurement in the report.",
      "paved_road": "Replace case-03 with a new generate case that has its own input, base, candidate and requested position and scale (a good placement, or a different break such as clipped, duplicated, seams or wrong scale), then label it with `uv run python -m eval.visual_harness label`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "eval/visual/case-04/case.json",
      "line": 4,
      "message": "case-04 is an exact copy of case-02: same case.json blob 65850ced, same input and base images, and same candidate.png b60324fe. Criterion 3 needs at least 6 generate cases, and copies only meet it on paper.",
      "paved_road": "Redraw case-04 as a separate generate case with its own composite and criterion, then relabel it through the panel.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "eval/visual/case-06/case.json",
      "line": 4,
      "message": "case-06 is a third exact copy of case-02: same case.json blob 65850ced, same input and base images, and same candidate.png b60324fe. The six generate cases contain only two distinct image sets.",
      "paved_road": "Redraw case-06 as a separate generate case, so the set holds at least 6 different generate cases that include good placements and different kinds of break.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "eval/visual/case-05/case.json",
      "line": 4,
      "message": "case-05 uses the same images and the same criterion as case-01 and case-03 (candidate 5e3cad69), but its label is `accept` while theirs are `reject`. Identical inputs carry opposite ground truth, so none of the generate cases is a clearly good placement, which the ticket's 'good and the broken placements' asks for.",
      "paved_road": "Draw a candidate whose placement plainly meets its stated position and scale, so the good case differs visibly from the broken ones, and let the panel label it. Do not keep identical cases that carry opposite labels.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "eval/visual/case-20/case.json",
      "line": 4,
      "message": "case-20's candidate.png (6732d350) is the same file as case-13's, and its criterion only rewords case-13's. It adds no new image to the 20-case minimum and repeats one measurement in the report.",
      "paved_road": "Replace case-20 with a new candidate image, for example a missing element, an off-position shape or a clipped object, label it through the panel, and rerun `./dev.py visual-baseline` so the report covers the corrected set.",
      "kind": null,
      "unit": null
    },
    {
      "code": "acceptance",
      "path": "eval/visual_report.json",
      "line": 2,
      "message": "The report's 20 cases include the duplicate cases listed above, so its overall and per-row agreement do not measure 20 distinct cases.",
      "paved_road": "After the duplicates are replaced and labelled, run `./dev.py visual-baseline` once over the final set and commit the regenerated report.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.8",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
