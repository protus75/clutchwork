---
id: declined-box-000898-9929dabd
kind: declined
link: box-000898-9929dabd
reopen_after_days: 30
---
Section 4 of docs/annotations-index-plan.md says the post-merge index build in serve and drain runs only for the paths the merge changed. The merged builder (`clutch/index.py::build`) instead lists every tracked .md/.py file with `git ls-files` and hashes each one on every build. It skips re-indexing only files whose hash has not changed.

This is a mismatch between the plan's wording and how the code works. It does not cause wrong runtime behavior. Because the builder skips files with an unchanged hash, a whole-tree pass produces the same index as a changed-paths pass. The only extra cost is reading and hashing the unchanged files. The message reports no wrong index contents, no merge or serve stall, and no measured build time that harmed a run. Reopen if a post-merge index build is shown to delay merges or serve dispatch by a measured amount, or if the index ends up with wrong or stale rows because of the whole-tree scan.

- docs/annotations-index-plan.md:117 says an unchanged-hash file is skipped and the build runs at merge end 'for the changed paths'
- clutch/index.py:293-315 builds from `git.ls_files(root)`, compares each file's sha256 against the stored `files.hash`, and re-indexes only files whose hash changed
- The message (origin index-merge-hook, stage implement, outcome ok) cites no failure, latency figure or incorrect index row

Message: box-000898-9929dabd
