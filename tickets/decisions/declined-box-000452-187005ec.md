---
id: declined-box-000452-187005ec
kind: declined
link: box-000452-187005ec
reopen_after_days: 30
---
During its Implement run, provider-failure-single-mapper warned that docs/roadmap.md would still describe the removed run_stages provider-exception mapper as current code. That ticket has since merged, and the roadmap now refers to the mapper as former and marks the ticket done.

This is documentation wording, not a runtime behavior gap. It also no longer applies. docs/roadmap.md calls the mapper 'former' and says 'No mapper covers stage operations', and it marks provider-failure-single-mapper done. Registry record declined-box-000447-54115f00 declined a similar note about planning docs left stale after a merged fix. Reopen if a current doc still describes the run_stages mapper as live and that text leads an operator or agent to take a wrong action.

- docs/roadmap.md:56 row 8: 'The former `run_stages` provider-exception mapper had no production caller ... No mapper covers stage operations; the driver maps their provider failures | `provider-failure-single-mapper` (done)'
- docs/roadmap.md:128: 'The former stage mapper had no production caller ... formerly `stages.run_stages` | `provider-failure-single-mapper` (done)'
- provider-failure-single-mapper is in the merged set
- Similar stale-planning-doc note declined as declined-box-000447-54115f00

Message: box-000452-187005ec
