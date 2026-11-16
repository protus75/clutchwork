# Review: snag

The schema, config and doc changes meet the ticket, but the store has four logic defects: put_blob loses non-UTF-8 bytes, prune can delete blobs that newer records still use, prune's run time grows with the square of the record count, and a normalized events file can hold only one event.

## Findings

- [logic] clutch/evidence/store.py:34 put_blob always decodes the bytes with errors="replace" and stores the re-encoded text. Any input that is not valid UTF-8 is changed for good: invalid bytes become U+FFFD, and get_blob(ref) returns those changed bytes instead of the data that was put. That breaks the round-trip AC5 asks for, and the stdout_times blob is a list of nanosecond offsets that may well be binary. Different invalid inputs can also collapse to one ref. (do instead: Decode with errors="strict". If decoding succeeds, run the redactor on the text and hash the re-encoded result. If it raises UnicodeDecodeError, hash and store the raw bytes unchanged. Add a test that puts non-UTF-8 bytes and checks get_blob returns them exactly.)
- [logic] clutch/evidence/store.py:81 prune collects references only from end.json files. When it decides whether a newer record still uses a blob, it ignores start.json (prompt.blob), normalized/*.json (args_blob, output_blob, text_blob) and calls that have a start.json but no end.json yet. Blobs are content-addressed and deduplicated, so a blob listed in the oldest end.json can be the same blob as a newer record's prompt, a normalized view's blob, or the output of a call still running. prune deletes it and leaves that newer record pointing at a missing blob. The ticket says a blob referenced by a newer record stays. (do instead: Build the set of protected refs from every file under calls/<key>/ (start.json, end.json and normalized/*). Only delete refs that appear in the oldest end.json and in no newer record and no in-flight call.)
- [logic] clutch/evidence/store.py:96 For each record, prune builds the union of the refs of every newer record again, so its cost is O(n^2) in the number of records. The design runs prune after every end.json write, and a store near the 20 GB bound can hold tens of thousands of calls, so each prune would do billions of set operations. (do instead: Count how many records reference each blob (or build the newer-ref sets once, walking from newest to oldest). Then walk the records from oldest to newest, decrementing counts, and delete a blob when its count reaches zero.)
- [logic] clutch/evidence/store.py:52 write_record("event") writes one Event as the whole calls/<key>/normalized/<normalizer>.json file. FileSystem.publish refuses an existing destination, so writing a second event for the same call and normalizer raises FileExistsError. The design (Record layout, section 3) says that file holds the normalizer's list of events, so this path cannot store a real normalized view. (do instead: Have the event record path take and validate a list of Event models and write it as one file, or drop the event case from write_record and read_record until the normalizer ticket defines that file's format.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "4a36c959e9d755824b65794af7cf907610d558ad",
  "stem": "evidence-store",
  "reviewed_sha": "4a36c959e9d755824b65794af7cf907610d558ad",
  "summary": "The schema, config and doc changes meet the ticket, but the store has four logic defects: put_blob loses non-UTF-8 bytes, prune can delete blobs that newer records still use, prune's run time grows with the square of the record count, and a normalized events file can hold only one event.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/evidence/store.py",
      "line": 34,
      "message": "put_blob always decodes the bytes with errors=\"replace\" and stores the re-encoded text. Any input that is not valid UTF-8 is changed for good: invalid bytes become U+FFFD, and get_blob(ref) returns those changed bytes instead of the data that was put. That breaks the round-trip AC5 asks for, and the stdout_times blob is a list of nanosecond offsets that may well be binary. Different invalid inputs can also collapse to one ref.",
      "paved_road": "Decode with errors=\"strict\". If decoding succeeds, run the redactor on the text and hash the re-encoded result. If it raises UnicodeDecodeError, hash and store the raw bytes unchanged. Add a test that puts non-UTF-8 bytes and checks get_blob returns them exactly.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/evidence/store.py",
      "line": 81,
      "message": "prune collects references only from end.json files. When it decides whether a newer record still uses a blob, it ignores start.json (prompt.blob), normalized/*.json (args_blob, output_blob, text_blob) and calls that have a start.json but no end.json yet. Blobs are content-addressed and deduplicated, so a blob listed in the oldest end.json can be the same blob as a newer record's prompt, a normalized view's blob, or the output of a call still running. prune deletes it and leaves that newer record pointing at a missing blob. The ticket says a blob referenced by a newer record stays.",
      "paved_road": "Build the set of protected refs from every file under calls/<key>/ (start.json, end.json and normalized/*). Only delete refs that appear in the oldest end.json and in no newer record and no in-flight call.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/evidence/store.py",
      "line": 96,
      "message": "For each record, prune builds the union of the refs of every newer record again, so its cost is O(n^2) in the number of records. The design runs prune after every end.json write, and a store near the 20 GB bound can hold tens of thousands of calls, so each prune would do billions of set operations.",
      "paved_road": "Count how many records reference each blob (or build the newer-ref sets once, walking from newest to oldest). Then walk the records from oldest to newest, decrementing counts, and delete a blob when its count reaches zero.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "clutch/evidence/store.py",
      "line": 52,
      "message": "write_record(\"event\") writes one Event as the whole calls/<key>/normalized/<normalizer>.json file. FileSystem.publish refuses an existing destination, so writing a second event for the same call and normalizer raises FileExistsError. The design (Record layout, section 3) says that file holds the normalizer's list of events, so this path cannot store a real normalized view.",
      "paved_road": "Have the event record path take and validate a list of Event models and write it as one file, or drop the event case from write_record and read_record until the normalizer ticket defines that file's format.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
