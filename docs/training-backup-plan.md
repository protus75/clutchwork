<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: Training data backup to Google Drive: plan
relates: [clutch/training.py, clutch/evidence/store.py, clutch/config.py]
owner: clutch/training.py
verified: 0bb2f0ee
hash: a0c35dd9bb6458725d00832105ad7214f1e974639a9c0927128b3ee0e731bdf9
-->
# Training data backup: plan

Back up a host's training data to Google Drive so it survives the checkout. Today the only copy lives under `.clutch/state/` (gitignored): deleting or re-cloning the checkout loses every record the host's runs produced (`docs/training-data-plan.md`). This plan adds one verb that copies the data to a Drive folder, append-only and deduplicated, safe for several clones of the same project writing at once.

Owner request, 2026-11-22: a backup of the export to Google Drive; a configurable path that defaults to one containing the host project's name; two clones can both write without a clash or an overwrite; repeated backups carry no duplicates; the Google access works as in `../fungo` (`fungo/docs/BACKUP_PLAN.md`), but the copy and preservation model is this plan's, not fungo's sync-and-versions model. Whether raw evidence is included is a flag on each run, not a setting chosen up front.

## Status

Draft, 2026-11-22. Not scheduled: the four tickets in "Ticket breakdown" are needed to deliver this plan, but no roadmap row or ticket exists until the owner chooses to add backup. Nothing is authored automatically. Related: `evidence-never-prunes` (ticket, 2026-11-22) stops the evidence store from silently deleting call outputs, which this plan's `--evidence` option would otherwise back up only partially.

## Requirements

1. **Never lose, never overwrite.** A backup only adds files to Drive. It never deletes, replaces, or renames a remote file. A failed or interrupted run leaves every earlier backup intact and is safe to rerun.
2. **No duplicates across runs.** Running backup twice with no new data uploads nothing the second time. A record already backed up is not uploaded again, even if a later export renders it with extra fields.
3. **Clones never clash.** Two clones of the same project (same repo name) can back up to the same Drive folder, at the same time, and neither can overwrite or corrupt the other's data.
4. **Configurable path, safe default.** The Drive location is a setting. The default includes the project name so different projects never share a folder by accident.
5. **Choose content per run.** Records only by default; `--evidence` adds the raw evidence store on that run.
6. **No hand-typed rclone.** Setup and backup are `clutch` verbs (CLAUDE.md "Guides name verbs, not command lines").

## Target design

### Transport and access (as in fungo)

- rclone, from the `rclone-bin` Python package, run through an argv wrapper module (`clutch/rclone.py`), never a shell (CLAUDE.md "Pure Python"). `rclone-bin` ships as an optional extra, `clutch[backup]`; the verb refuses with the install command when it is missing.
- One rclone remote of type `drive` with scope `drive.file` (rclone sees only files it created). The owner's own Google Cloud OAuth client (Desktop app, consent screen published to production, unverified), not rclone's shared client, exactly as `fungo/docs/BACKUP_PLAN.md` "OAuth client" describes.
- The rclone config holds the OAuth token and client secret. It lives outside the repo and is never committed or passed on a command line. Default: the per-user config directory (`~/.config/clutch/rclone.conf`), so every clone on the machine shares one sign-in; overridable by setting. (Open decision 1.)
- `clutch backup setup` creates the remote interactively (client ID and secret prompted, browser sign-in), writes the config file, and verifies access with one listing.

### Where data goes

```
<remote>:<root>/<project>/
  clones/<clone-id>/records/<UTC timestamp>-<n>.jsonl   # append-only record batches
  clones/<clone-id>/index/<UTC timestamp>-<n>.txt       # record keys in the matching batch
  evidence/blobs/<sha256>                               # --evidence: content-addressed blobs
  evidence/clones/<clone-id>/calls/...                  # --evidence: per-clone call records
```

- `<remote>:<root>` comes from config `backup.remote` (default `gdrive:clutch-training`).
- `<project>` defaults to `<repo name>-<first 8 hex of sha256(origin URL)>`; with no `origin` remote, the repo directory name alone. The hash keeps two unrelated projects that share a name apart. Overridable by `backup.project`. (Open decision 2.)
- `<clone-id>` is a random ID generated once per clone and stored in `state_dir` (gitignored, so a fresh clone gets a fresh ID). A clone writes only under its own `clones/<clone-id>/`; that is what makes clones unable to clash. Blobs are shared because a blob's name is its content hash: two clones writing the same name write the same bytes.

### Deduplication

- **Record key:** `sha256(clone-id, kind, sorted call_keys, label)`. It is stable across re-exports of the same record and differs between clones (whose call keys can coincide, since keys are `llm/<stem>/<run>/<surface>/<attempt>/<n>`). The record body is not part of the key, so a re-export that adds fields does not create a duplicate. The first upload of a key wins. (Open decision 3.)
- **What is already uploaded:** the union of this clone's `index/*.txt` files. Backup lists only its own `index/` folder (small) rather than every record, and keeps a local cache of that union in `state_dir`, rebuilt from the remote when missing.
- **One run:** export to a temporary directory with the existing `training export` machinery; drop records whose key is in the index; write the remaining records as one new batch file plus its index file; upload both with rclone `copyto` and flags that refuse to overwrite (`--immutable`, `--ignore-existing`). The batch is uploaded before its index, so an interrupted run at worst re-uploads that batch's records next time under a new batch name: a duplicate within one clone that the key filter removes on read, never a loss. (Open decision 4.)
- **Evidence (`--evidence`):** blobs upload by content-hash name with `--ignore-existing` (re-runs skip them for free). Call records upload under the clone's own folder with `--immutable`, so a changed local record is reported and skipped, never overwritten.

### Verbs

A new top-level `backup` group, modelled on `clutch provider install` / `clutch provider probe`: the operator never types an rclone command, and README and the host guides name only these verbs (CLAUDE.md "Guides name verbs, not command lines").

- `clutch backup install`: installs or updates `rclone-bin` into the clutch environment (the `clutch[backup]` extra) and reports the rclone version, as `provider install` does for provider CLIs.
- `clutch backup setup`: one-time remote creation (OAuth client ID and secret prompted, browser sign-in) and the rclone config file.
- `clutch backup probe`: checks that rclone runs, the config exists, and the remote folder is reachable and writable; non-zero with the paved road when not.
- `clutch backup run [--evidence] [--dry-run]`: one run as above. Prints counts (new records, skipped as already backed up, blobs uploaded, bytes) and the remote path. Exit codes per CLAUDE.md "Command help". Reads the store and journal.
- `clutch host doctor` gains a backup row (rclone present, config present, last backup time), warning, never failing, when backup is unconfigured or stale.
- A last-backup line in `clutch view status` (time, records, remote path), read from a marker in `state_dir`.

## Not in scope

- Restore and merge. Reading backups back (for training on another machine) is a later verb; the layout above is designed so that a reader takes the union of all clones' batches and drops duplicate keys. (Open decision 5.)
- Scheduling. Backups run by hand or from a host's own job.
- Other targets. S3 or any rclone remote works by changing `backup.remote`; nothing here is Drive-specific except the setup verb.

## Ticket breakdown (authored when the owner schedules backup)

1. `backup-rclone-seam`: `clutch/rclone.py` argv wrapper, the `clutch[backup]` extra, the `backup` config block (`remote`, `project`, `rclone_config`), clone ID, project-name default, and the `backup` group with `install`, `setup` and `probe`, plus the doctor row.
2. `backup-records`: `backup run` for records: export to temp, key filter, batch and index upload, local index cache, counts, `--dry-run`, last-backup marker and status line.
3. `backup-evidence-option`: `--evidence` blob and call-record upload.
4. `backup-docs`: host guide section (setup, what is backed up, Drive folder layout, changing OAuth clients re-uploads, as in fungo), verb tables, README.

## Risks

- **Changing the OAuth client hides earlier backups.** `drive.file` shows a client only the files it created, so a new client starts a new folder and uploads in full. The guide says so, as fungo's does.
- **Drive is slow with many small files.** Records go up in batches, not one file per record. Evidence blobs are one file each; the first `--evidence` run can be slow.
- **Secrets.** Export already scrubs records (`clutch/training.py` `_safe`). Evidence blobs are stored redacted by the evidence store. The rclone config with the token never enters the repo or a backup.

## Open decisions

1. **rclone config location.** Proposed: per-user `~/.config/clutch/rclone.conf` (one sign-in shared by every clone and project on the machine). Alternative: repo-local `.rclone.conf` as in fungo (one sign-in per clone).
2. **Project folder name.** Proposed: `<repo name>-<8-hex origin hash>`. Alternative: repo name alone, as requested, accepting that two unrelated projects with one name would share a folder (still no overwrite, since clone IDs differ).
3. **Record key.** Proposed: clone ID, kind, call keys, label, ignoring the body. Alternative: a content hash of the canonical record, which re-uploads a record whenever export adds a field.
4. **Batch granularity.** Proposed: one batch file per run. Alternative: one file per record (simplest dedup, slow on Drive).
5. **Restore.** Proposed: a later `clutch backup pull` that merges every clone's batches by key. Not part of this plan's tickets.
