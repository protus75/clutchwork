---
id: declined-box-000630-6cc9971a
kind: declined
link: box-000630-6cc9971a
reopen_after_days: 30
---
The release-changelog Implement run found that docs/roadmap-driver-plan.md still says a release commit holds only pyproject.toml and uv.lock. Once release-changelog lands a changelog file in that commit, the statement is out of date. The run could not fix it because the planning document was outside its scope fence.

This is wording in a planning document that no longer matches the code. Nothing in the engine reads or enforces that sentence, so no runtime behavior is wrong. The registry has declined the same kind of out-of-fence planning-doc staleness several times (000526, 000530, 000533, 000621, 000622, 000624, 000627). Reopen if some engine code, gate or test starts parsing roadmap-driver-plan.md for what a release commit contains, or if an operator or agent run is misled by the sentence into a wrong release action.

- message class suggestion, origin release-changelog, stage implement, outcome ok
- release-changelog is in the merged set
- declined-box-000526-6842d927, declined-box-000530-c9630ad6 and declined-box-000533-3ff8c951 declined stale roadmap-driver-plan.md and roadmap wording reported from out-of-fence Implement runs

Message: box-000630-6cc9971a
