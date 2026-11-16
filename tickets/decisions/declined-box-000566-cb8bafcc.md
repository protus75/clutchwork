---
id: declined-box-000566-cb8bafcc
kind: declined
link: box-000566-cb8bafcc
reopen_after_days: 14
---
The note asks to replace the rejected test-gate-floors ticket (roadmap row 22) with a new stem whose coverage floors come from measurement. Its rule 'measured minus 2, never below 1' cannot be met because the unit check measures clutch/covmap.py, clutch/doctor.py and clutch/thresh.py at exactly 0%. The proposed values: graph.py 96; audit, observe, seams, stats and watchdog at measured minus 2; the three integration-only modules stay at 0 with a comment. It also suggests one roadmap ticket that re-files rows 19, 21 and 22 together, and an authoring rule that floor-setting tickets cite unit coverage measured with the unit check's own argv.

Nothing at runtime is behaving wrongly here. Today the floors sit at 0 or at the 90 default. That means a regression could go unnoticed, but nothing currently fails or gives a wrong result. Raising them is a gate and test-only hardening change, which the admission bar declines unless it is tied to reachable incorrect behavior. A rejected roadmap row that the driver will not re-author also matches the row-21 re-file request already declined in declined-box-000560-b39d4505. Row 19 got a re-file ticket (closed-sets-single-owner-refile) only because graphics-kind depends on its stem and stays blocked for good. The note names no ticket that depends on test-gate-floors. The proposed authoring rule about measured coverage is a prevention idea from one rejection, not an observed recurring failure. It is not a duplicate: test-gate-floors is the rejected ticket this note would replace. Reopen if a roadmap row or open ticket that depends on row 22's stem is shown to be stuck, if a module in the listed set loses coverage without any gate failing, or if a second floor-setting ticket is rejected or parks on unmeasured floors.

- Open ticket test-gate-floors: its goal requires positive floors for eight floor-0 modules; the message reports covmap/doctor/thresh measure 0.00% under the unit check at 18ae4ba9
- declined-box-000560-b39d4505 declined the analogous roadmap row 21 re-file request
- closed-sets-single-owner-refile was justified by graphics-kind (row 49) depending on the rejected stem; no such dependent is cited for row 22
- Message names no runtime defect; the harm is the absence of coverage protection, a gate/test-only concern

Message: box-000566-cb8bafcc
