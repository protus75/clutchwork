---
id: declined-box-000525-7a27ac24
kind: declined
link: box-000525-7a27ac24
reopen_after_days: 30
---
On 2026-11-16, interactive `clutch review supervisor-rework` runs of requisition review hit the 10-minute per-call stuck budget 5 times out of 8, while the other 3 finished in about 8 to 8.5 minutes. The message predicts that the drain's own requisition stage would time out the same way and spend the ticket's caps. It proposes a stuck budget that grows with prompt size, or a timeout outcome that draws no caps.

The timeouts in the interactive review loop are real: engine.log shows 5 `requisition_review` stage_end events with outcome `timeout`, each exactly 10 minutes after stage_start. The harm the message predicts did not happen. The drain's requisition review of supervisor-rework (run_seq 0, 06:41) ended `ok` in about 3m20s, and supervisor-rework is now merged. No ticket spent caps, parked, or was rejected because requisition review timed out. What remains is a slow interactive loop for one large ticket, which is not a current runtime failure that damages work. Reopen if a drain or serve requisition_review `timeout` draws a ticket's retry, infra, or premise_bounce cap, or sends a reviewable ticket to the Reject queue or a park.

- .clutch/state/engine.log lines 12297-12429: supervisor-rework requisition_review stage_end outcome=timeout at run_seq 28809, 28876, 28959, 28994 and 29028, each exactly 10m after its stage_start
- .clutch/state/engine.log lines 12280-12385: the completed reviews (gate_failed) took about 8m to 9m24s
- .clutch/state/engine.log lines 12618-12619: the drain requisition_review for supervisor-rework at run_seq 0 ended ok in about 3m20s
- supervisor-rework is in the merged stems list, so the predicted cap spend never happened

Message: box-000525-7a27ac24
