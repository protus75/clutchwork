---
id: tombstone-box-000907-addb0196
kind: tombstone
link: implement-spec-meta-headers-from-verbs
reopen_after_days: 14
---
Implementers keep writing `clutch:meta` headers by hand, and each malformed header costs a full attempt. On spools-test-helper attempt 0, the two new test files' headers had no `verified` or `hash` lines, so `clutch/meta.py` parse raised Malformed and Review failed the attempt. The note proposes two fixes: tell agents to create headers through the engine verb and edit only the purpose line, or have Check repair a malformed block in a new file.

The open ticket implement-spec-meta-headers-from-verbs already covers this gap, citing the same spools-test-helper attempt 0 evidence: both new files lacked `verified` and `hash`, and parse raised Malformed. After that ticket, the Implement prompt tells implementers to get a header for a new file only from `clutch meta fill <path>` or `clutch meta refresh`, never to type one, and to run `clutch meta check` after the last edit. That is the message's first proposed fix. The empty-purpose trailing space it also mentions (box-000888) was fixed by the merged meta-render-empty-purpose-no-trailing-space. The second proposal, having Check repair malformed blocks in new files, is a different way to fix the same gap and does not need its own ticket. Reopen if hand-typed header failures continue after implement-spec-meta-headers-from-verbs merges.

- Open ticket implement-spec-meta-headers-from-verbs cites spools-test-helper attempt 0: Review snagged both new files because their headers lacked `verified` and `hash`, so `clutch/meta.py::parse` raised Malformed.
- That ticket tells implementers to get a header only from `clutch meta fill <path>` or `clutch meta refresh` and to run `clutch meta check` after the last edit.
- Merged ticket meta-render-empty-purpose-no-trailing-space fixed the empty-purpose trailing space related to box-000888.

Message: box-000907-addb0196
