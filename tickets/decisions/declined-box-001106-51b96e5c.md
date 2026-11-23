---
id: declined-box-001106-51b96e5c
kind: declined
link: box-001106-51b96e5c
reopen_after_days: 30
---
Some reads in clutch/stages.py still go straight to disk instead of through the ctx.fs seam: ticket.md, run.md, worktree file bytes and the review ticket. Because of this, a whole stage run cannot be driven on FakeFileSystem in a test. The note says io-helpers-stages lost one attempt to this and asks that those reads go through ctx.fs.

In production these reads return the right bytes, so nothing goes wrong at runtime. The gap only limits fake-driven tests, which makes it test-infrastructure and seam-hygiene work, not a behavior defect. Registry record 000120 declined the same kind of request for merge.read_candidate reading ticket.md and review.md with Path.read_text instead of the seam. Record 000025 declined the same for config loading. The ticket this note cites, io-helpers-stages, has already merged, so the lost attempt bought no current harm. Reopen if a stage run produces wrong runtime behavior because these reads bypass the seam. Also reopen if a confirmed ticket's acceptance criteria require running a stage on FakeFileSystem and the ticket fails Implement or Check for that reason; in that case, file it with the failing run's evidence.

- The message cites direct disk reads in clutch/stages.py but no wrong runtime output
- Declined record 000120 covers the same seam-bypass pattern for read_candidate in clutch/merge.py
- Declined record 000025 covers the same pattern for config.py load_config reading straight from disk
- io-helpers-stages is in the merged set, so the attempt it lost does not block current work
- Neighbor index unavailable (index_unreadable)

Message: box-001106-51b96e5c
