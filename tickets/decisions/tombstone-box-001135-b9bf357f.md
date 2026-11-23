---
id: tombstone-box-001135-b9bf357f
kind: tombstone
link: declined-box-001131-43b6d880
reopen_after_days: 30
---
A retro-calibration-manual Implement run reports that docs/roadmap.md (line 360) still says calibration runs automatically at the engine idle point. That change made calibration manual. The run left the plan document alone because it was outside the ticket's scope fence.

Registry record declined-box-001131-43b6d880 already covers this exact report: the same run (retro-calibration-manual) flagged the same stale idle-calibration wording in the same file (docs/roadmap.md). That record declined it because stale wording in a forward-looking plan document causes no wrong runtime behavior. This message adds only a line number.

- declined-box-001131-43b6d880: the retro-calibration-manual run warned that docs/roadmap.md still describes calibration running automatically at the engine idle point
- This message has the same origin (retro-calibration-manual), the same file (docs/roadmap.md:360) and the same stale claim (automatic idle calibration)
- Similar plan-document staleness reports (for example 001125, 001127 and 001130) were declined because plan wording does not drive runtime behavior

Message: box-001135-b9bf357f
