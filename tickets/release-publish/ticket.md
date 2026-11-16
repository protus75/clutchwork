---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- release-verb

## Runs before
- update-config-unverified-empty-listing

## Context
- clutch/release.py
- clutch/git.py::Git.rev_parse
- clutch/git.py::Git.status_porcelain
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/providers.py::secret_names
- clutch/providers.py::child_env
- clutch/redact.py
- clutch/config.py::Config
- clutch/journal.py::SIGNAL_NAMES
- clutch/seams.py::FileSystem
- dev.py
- tests/unit/test_release.py
- tests/integration/test_release.py
- tests/integration/test_dev.py
- tests/integration/test_cli.py::ENV
- tests/integration/test_cli.py::CONFIG
- tests/integration/test_host_contract.py::test_host_contract_schema_coverage
- tests/integration/test_closed_sets.py::test_journal_closed_sets_and_constants
- clutch/docs/host-running.md
- clutch/docs/host-contract.md#Complete field inventory
- docs/how-clutch-works.md#2.1
- docs/how-clutch-works.md#2.2
- docs/how-clutch-works.md#8.1
- docs/how-clutch-works.md#11.
- docs/roadmap-driver-plan.md#5.

## Goal / Why
`clutch release --minor|--patch` (merged by `release-verb`) bumps, commits, and tags a release locally, but nothing publishes it. The only upload road is `./dev.py publish`, which runs `uv version --bump patch` before it builds (`dev.py::main`, `publish` branch). After `clutch release --minor` tags `v0.4.0`, `./dev.py publish` would upload `0.4.1`: an uncommitted, untagged version, while the tagged release never reaches PyPI (Suggestion Box message `box-000480-aef03519`). `./dev.py publish` also reads `UV_PUBLISH_TOKEN` from the environment that every clutch child inherits: `clutch/providers.py::child_env` removes only provider `auth` names, so a token exported for publishing reaches git, every check, and every provider CLI, including Implement's write-enabled agent. That breaks `CLAUDE.md` section A, "Never pass a provider key to a process that does not need it".

`docs/roadmap-driver-plan.md` section 5 (roadmap row 92) has `clutch publish` upload to PyPI only under the owner's standing authorization `release.publish: true`, with the token's env var name in config (`release.pypi_token`). The token is passed to the upload child only, like a provider key. `clutch release` journals a `release` signal; `release-verb` left that signal to this row. The owner's decision for unattended runs replaces the plan's "park for `confirm`": when `release.publish` is absent or false, `clutch publish` builds and lists the artifacts and uploads nothing. `release.publish` defaults to false.

After this change:
1. `config.yaml` accepts a `release` block, `{publish: false, pypi_token: UV_PUBLISH_TOKEN}` by default. The env var that `release.pypi_token` names is a configured secret. Like a provider `auth` name, `child_env` removes it from every child process and the redactor scrubs its value from captured streams.
2. `uv run clutch publish` takes the writer lock and refuses (exit 2) in these cases: `release.publish` is true and the token env var is unset; a tracked file has uncommitted changes, because `uv build` packages the working tree and the upload must equal the tagged commit; or the version `uv version --short` reads has no `v<version>` tag on HEAD. The tag refusal's paved road names `clutch release`. Publish never bumps, commits, or tags. It then builds the wheel and sdist into `<state_dir>/dist` and prints each path. With `release.publish: true`, it uploads them with `uv publish`, the only child process that receives the token (as `UV_PUBLISH_TOKEN`). Otherwise it says that nothing was uploaded and how to enable uploads. Both paths exit 0.
3. `clutch release` also journals `{"signal": "release", "version", "tag", "commit"}` once it has tagged. The roadmap driver reads that record when it decides a release is done.
4. `./dev.py publish` is gone. `CLAUDE.md` section B makes `./dev.py` hold only this repo's build and release tasks, while an engine task is a `clutch` verb ("A missing engine task becomes a new `clutch` verb"). PyPI publishing is now an engine task that hosts also use, so a `dev.py` twin would be a second, divergent upload path. This repo publishes with `uv run clutch publish`.

## Scope in / Scope out
Scope in:
- `clutch/config.py`: a new `Release(_Strict)` model with `publish: bool = False` and `pypi_token: str = "UV_PUBLISH_TOKEN"`, and a `release: Release = Release()` field on `Config`. The schema version does not change: the block is optional and defaults when absent.
- `clutch/redact.py`: gains `secret_names(config)`, moved from `clutch/providers.py`, where `child_env` is its only caller. It returns every provider `auth` name plus `config.release.pypi_token`. `Redactor.from_config` resolves exactly the names `secret_names(config)` returns that are set in `env`, and its docstring says so. `clutch/providers.py` deletes its own `secret_names`, and `child_env` imports `secret_names` from `clutch.redact`; `providers.py` already imports `Redactor` from there. The `child_env` docstring says it removes every configured secret. Nothing else in `providers.py` changes.
- `clutch/release.py`: a new `async def publish(repo, git, exec_, fs, env, config) -> tuple[str, list[Path], bool]` returning the version, the artifact paths, and whether it uploaded. `env` is the parent environment and `config` the loaded config. It runs these steps in order:
  1. When `config.release.publish` is true and `env` has no non-empty value for `config.release.pypi_token`, raise `runner.Refusal`. The message names that env var; the road is to export it with a PyPI token or to set `release.publish: false` to build without uploading. No exec call happens first.
  2. Compute `child = child_env(env, config)`, imported from `clutch.providers`. Every child below except the upload gets exactly `child`.
  3. Run `git.status_porcelain(repo, "--untracked-files=no")`. Non-blank output raises `Refusal` naming the reported paths, with the road to commit or restore them and retry `clutch publish`.
  4. Run `["uv", "version", "--short"]` through `exec_` (cwd `repo`, timeout `UV_TIMEOUT_S`). A non-zero exit raises `Refusal` carrying the last non-blank stderr line, as `release` does. The version is the stripped stdout.
  5. Read `git.rev_parse(repo, "HEAD")` and `git.rev_parse(repo, f"refs/tags/v{version}^{{commit}}")`. A `GitError` from the tag read, or a tag commit different from HEAD, raises `Refusal` naming `v<version>`. The road is to run `clutch release --minor` or `clutch release --patch` to tag the version at HEAD, then retry `clutch publish`.
  6. Run `["uv", "build", "--clear", "-o", str(config.state_dir / "dist")]` through `exec_`, with a finite module-level timeout. A non-zero exit raises `Refusal` carrying the last non-blank stderr line.
  7. The artifacts are `fs.entries(dist)` names ending in `.whl` or `.tar.gz`, in that sorted order, as paths under `dist`. `uv build` also writes a `.gitignore` there, which is never an artifact. No artifact raises `Refusal`.
  8. When `config.release.publish` is false, return `(version, artifacts, False)`.
  9. Otherwise run `["uv", "publish", *map(str, artifacts)]` through `exec_` with env `{**child, "UV_PUBLISH_TOKEN": env[config.release.pypi_token]}` and a finite module-level timeout. The token never appears in an argv. A non-zero exit raises `Refusal` carrying the last non-blank stderr line. Return `(version, artifacts, True)`.
  `release.release` does not change.
- `clutch/__main__.py`:
  - `_parser` gains a `publish` subcommand with no arguments (help: build the tagged release and upload it when `release.publish` is true).
  - In `main`, a `publish` branch beside `release` locks as `release` does (`Lockfile(config.state_dir, verb="publish", ...)`, released in a `finally`). It calls `release.publish(repo, checkout.git, checkout.exec_, checkout.fs, env, config)`, looked up on the `clutch.release` module at call time. It prints `publish: built <path>` for each artifact. It then prints `publish: uploaded <version> to PyPI`, or, when nothing was uploaded, `publish: release.publish is false; uploaded nothing -- set release.publish: true in config.yaml to upload`. It returns 0.
  - The `release` branch, inside the lock and right after `release.release` returns, appends `EventType.SIGNAL` with body `{"signal": "release", "version": version, "tag": f"v{version}", "commit": sha}` to `checkout.journal`. Nothing is journaled when `release.release` raises.
- `clutch/journal.py`: `"release"` joins `SIGNAL_NAMES`.
- `dev.py`: delete the `publish` subparser, its dispatch branch, and its docstring usage line. Keep an import only if something still uses it. `test`, `vscode`, `vscode-package`, and the bare suite run do not change.
- `CLAUDE.md` section B, the `Command surface` bullet: the task list becomes (`test`, `vscode`, `vscode-package`). The rule itself does not change. It is a rule about working on clutch itself, so its home is `CLAUDE.md` outside the managed block. `AGENTS.md` has no section B and does not change.
- `clutch/docs/host-running.md`:
  - a `publish` verb-table row (works while serve runs: No) saying it builds the release tagged at HEAD and uploads it only with `release.publish: true`, and that it never bumps;
  - `publish` joins the "Stop serve before ..." sentence's verbs.
- `clutch/docs/host-contract.md`, section Complete field inventory:
  - `Config.defaults` gains `release: {publish: false, pypi_token: UV_PUBLISH_TOKEN}`;
  - a new `Release` row (`required: []`, those defaults);
  - one prose sentence: `release.pypi_token` names an environment variable, never a literal token; it is removed from every child process and redacted like a provider `auth`; only `clutch publish`'s upload receives its value; `release.publish: true` is the owner's standing authorization to upload.
- `docs/how-clutch-works.md`:
  - section 2.1: a `publish` row (Lock: yes) describing the steps above; the `release` row adds that it journals a `release` signal;
  - section 2.2: delete the `publish` row;
  - section 8.1: the bullet on provider `auth` env vars adds that the env var `release.pypi_token` names is removed the same way, except from `clutch publish`'s `uv publish` child, which receives it as `UV_PUBLISH_TOKEN`;
  - section 10.1: a `dist/` row, because the table lists every path under `state_dir` and `clutch publish` adds this one. It holds the wheel and sdist `clutch publish` built last; `uv build --clear` empties it on each publish;
  - section 11: a `release` row in the config table.
  Nothing else in the file changes.
- Existing tests, each edited only as stated:
  - `tests/unit/test_release.py::test_main_release_locks_calls_and_prints`: replace `cli.Journal` with a recorder whose `append` does nothing, so the new signal append does not write under the fake `/state`. Its assertions stay as they are.
  - `tests/integration/test_closed_sets.py::test_journal_closed_sets_and_constants`: add `"release"` to the expected `SIGNAL_NAMES`.
  - `tests/integration/test_dev.py`: delete `test_publish_uploads_built_files` and `test_publish_refuses_without_token`. In `test_test_passes_leading_options_to_pytest`, the second half runs `["dev.py", "vscode-package", "--bogus"]` instead of `publish --bogus` and drops its `UV_PUBLISH_TOKEN` line. It still asserts `SystemExit` code 2 with no `dev.subprocess.run` call.
  - Fake configs that now reach `secret_names` through `child_env` or `Redactor.from_config` gain `release=SimpleNamespace(pypi_token="UV_PUBLISH_TOKEN")` (`NS(...)` in the first). There are four: `tests/unit/test_preflight_parallel.py::make_client`, the config in `tests/unit/test_probe_verb.py::test_probe`, the `SimpleNamespace(providers=[p])` in `tests/unit/test_qwen_adapter.py`'s adapter helper, and the config in `tests/unit/test_update_config_verb.py::test_verb`. A trial of this change at the base commit failed exactly these seven unit tests, in those four files, with `AttributeError: ... 'release'`. Nothing else in these files changes.
- New tests in two new files, `tests/unit/test_release_publish.py` and `tests/integration/test_release_publish.py`. The unit file defines its own fake exec, which records argv and env per call; the one in `tests/unit/test_release.py` asserts a fixed env, so it is not reused. The unit file may import `FakeLock`, `REPO`, and `SHA` from `tests/unit/test_release.py`. The integration file may import `CONFIG` and `ENV` from `tests/integration/test_cli.py` and the `repository` fixture from `tests/integration/test_release.py`, all unchanged.

Scope out:
- `./dev.py vscode-publish`, `release.vsce_token`, `vsce publish`, and any Marketplace upload. Azure DevOps global PATs, which `vsce publish` uses, retire on 2026-12-01 (`tickets/vscode-marketplace-publish/ticket.md`). The Marketplace road needs an owner decision, filed to the Suggestion Box.
- A `publish` journal signal, a park, or any `confirm` path for publishing. The roadmap driver's idle-point sequence and digest belong to `driver-loop`.
- Any change to `clutch/release.py::release`'s bump, commit, or tag behavior.
- Pushing commits or tags, TestPyPI or other index URLs, and `uv publish --check-url`.
- `vscode-clutchwork/`, `clutch/help.py`, `clutch/observe.py`: `publish` is not an extension surface, as `release` is not.
- `README.md`, `AGENTS.md`, `clutch/hostfiles.py`, `docs/roadmap.md`, and the plan documents under `docs/`.

## Scope fence
- clutch/config.py
- clutch/redact.py
- clutch/providers.py
- clutch/release.py
- clutch/__main__.py
- clutch/journal.py
- dev.py
- CLAUDE.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_release_publish.py
- tests/integration/test_release_publish.py
- tests/unit/test_release.py
- tests/unit/test_preflight_parallel.py
- tests/unit/test_probe_verb.py
- tests/unit/test_qwen_adapter.py
- tests/unit/test_update_config_verb.py
- tests/integration/test_closed_sets.py
- tests/integration/test_dev.py

## Acceptance criteria
1. `tests/unit/test_release_publish.py::test_publish_uploads_the_tagged_head` drives `clutch/release.py::publish` with `release.publish` true and `pypi_token` `PYPI_TOKEN`. The env holds `PYPI_TOKEN=pypi-secret`, a provider key `CLAUDE_KEY` named as a provider `auth`, and `PATH`. Git is built on the same scripted fake exec, and the fake `fs.entries` returns `.gitignore`, `host-0.4.0-py3-none-any.whl`, and `host-0.4.0.tar.gz` for `<state_dir>/dist`. The script: clean status, `uv version --short` printing `0.4.0`, HEAD and `refs/tags/v0.4.0^{commit}` both resolving to the same sha, build exit 0, upload exit 0. The test asserts:
   - the return is `("0.4.0", [dist/"host-0.4.0-py3-none-any.whl", dist/"host-0.4.0.tar.gz"], True)`;
   - the `uv` argvs are exactly `["uv", "version", "--short"]`, `["uv", "build", "--clear", "-o", str(dist)]`, `["uv", "publish", <wheel path>, <sdist path>]`, in that order;
   - no argv contains `--bump` or `pypi-secret`, and no git call's subcommand (the argv element after `-C <repo>`) is `commit`, `tag`, or `push`;
   - the upload call's env has `UV_PUBLISH_TOKEN == "pypi-secret"` and no `PYPI_TOKEN` or `CLAUDE_KEY`;
   - no other call's env contains `PYPI_TOKEN`, `UV_PUBLISH_TOKEN`, `CLAUDE_KEY`, or the value `pypi-secret`.
   Ruled out: a version bump, uploading `.gitignore`, the token on an argv, and the token reaching `uv version` or `uv build`.
2. `tests/unit/test_release_publish.py::test_publish_false_builds_and_uploads_nothing` runs the same script without the upload step. `release.publish` is false and the env has no token. It asserts the return `("0.4.0", [<wheel>, <sdist>], False)`, the version and build calls, and no `uv publish` call. Ruled out: an upload without `release.publish: true`, and a token refusal when nothing is uploaded.
3. `tests/unit/test_release_publish.py::test_publish_refuses_a_tag_not_on_head` covers two cases. In one the tag read fails (`rev-parse` exit 128); in the other it resolves to a sha other than HEAD's. In both, `publish` raises `runner.Refusal` whose text contains `v0.4.0` and `clutch release`, with no `uv build` or `uv publish` call. Ruled out: building or uploading a version whose tag is missing or sits on another commit, and a refusal without the `clutch release` road.
4. `tests/unit/test_release_publish.py::test_publish_refuses_dirty_tree_and_missing_token` covers two cases.
   - A status reporting ` M clutch/core.py` raises `Refusal` naming `clutch/core.py`, and the status call is the only exec call.
   - With `release.publish` true and `PYPI_TOKEN` absent from env, `publish` raises `Refusal` naming `PYPI_TOKEN` and `release.publish: false`, with no exec call at all.
   Ruled out: building over uncommitted tracked changes, and any git or uv call before a missing-token refusal.
5. `tests/unit/test_release_publish.py::test_publish_command_failures_refuse` covers four cases:
   - `uv version --short` exits 2 with stderr ending `error: No project`;
   - `uv build` exits 1 with stderr ending `error: build failed`;
   - `uv build` exits 0 but `fs.entries` returns only `.gitignore`;
   - with `release.publish` true, `uv publish` exits 1 with stderr ending `error: 403 Forbidden`.
   Each raises `Refusal`; the three failing commands' refusals contain their last stderr line. The first three cases make no `uv publish` call. Ruled out: an upload after a failed or empty build, and a refusal that drops uv's error.
6. `tests/unit/test_release_publish.py::test_release_token_is_a_configured_secret` asserts three things:
   - `config.Release().model_dump() == {"publish": False, "pypi_token": "UV_PUBLISH_TOKEN"}`;
   - with a config whose provider `auth` is `CLAUDE_KEY` and whose `release.pypi_token` is `PYPI_TOKEN`, `providers.child_env({"PATH": "/bin", "CLAUDE_KEY": "k", "PYPI_TOKEN": "pypi-secret"}, config)` equals `{"PATH": "/bin"}`;
   - `Redactor.from_config(config, that env).scrub("x pypi-secret y")` equals `"x [REDACTED:PYPI_TOKEN] y"`.
   Ruled out: publishing on by default, and a publish token that reaches git, checks, or provider CLIs or survives in a spool.
7. `tests/unit/test_release_publish.py::test_main_publish_locks_calls_and_prints` drives `clutch.__main__.main(["publish"], cwd=Path("/repo"), env={"PYPI_TOKEN": "pypi-secret"})` with `load_config`, `child_env`, `Lockfile`, and `Git.describe` faked as `tests/unit/test_release.py::test_main_release_locks_calls_and_prints` fakes them. `clutch.release.publish` is replaced by a recorder. The test asserts four things:
   - the recorder receives that env unchanged and the loaded config;
   - the lock verb is `publish`;
   - the order is acquire, then publish, then unlock;
   - stdout is exactly `publish: built /state/dist/a.whl`, `publish: built /state/dist/a.tar.gz`, then either `publish: uploaded 0.4.0 to PyPI` (fake returns `True`) or `publish: release.publish is false; uploaded nothing -- set release.publish: true in config.yaml to upload` (fake returns `False`).
   A third case raises `Refusal`: `main` returns 2, stderr starts `clutch publish:`, and the lock is still released. Ruled out: publishing without the lock, a lock left held, and wrong or missing output lines.
8. `tests/unit/test_release_publish.py::test_main_release_journals_the_release_signal` drives `main(["release", "--minor"], ...)` with the fakes of criterion 7, `clutch.release.release` returning `("0.2.0", SHA)`, and `cli.Journal` replaced by a recorder. It asserts exactly one append, `(EventType.SIGNAL, {"signal": "release", "version": "0.2.0", "tag": "v0.2.0", "commit": SHA})`, recorded after the release call and before unlock. When the fake release raises `Refusal`, nothing is appended. Ruled out: a missing signal, a signal written after the lock is released, and a signal for a refused release.
9. `tests/integration/test_release_publish.py::test_publish_passes_the_token_to_the_upload_only` builds a real git repo in `tmp_path`:
   - `config.yaml` is `CONFIG` plus `release: {publish: true, pypi_token: PYPI_TOKEN}`;
   - a committed `pyproject.toml` at `0.4.0`;
   - an annotated tag `v0.4.0` on HEAD.
   It monkeypatches `SubprocessExec.run` to record `(argv, env)` for every call. Git argvs pass to the real method. `uv` argvs are answered: `version --short` prints `0.4.0`; `build` writes `.gitignore`, a wheel, and an sdist into its `-o` directory; `publish` exits 0. `main(["publish"], cwd=repo, env=ENV | {"PYPI_TOKEN": "pypi-secret"})` returns 0 and prints two `publish: built <state_dir>/dist/...` lines, then `publish: uploaded 0.4.0 to PyPI`. The recorded calls include at least one git call. Exactly one recorded call has `pypi-secret` among its env values: the `uv publish` call, as `UV_PUBLISH_TOKEN`. No recorded argv contains `pypi-secret`. HEAD and the bytes of `pyproject.toml` are unchanged, and `Lockfile(state_dir, ...)` can be acquired afterwards. Ruled out: the token reaching git or the build through the real `main` wiring, and a bump or commit during publish.
10. `tests/integration/test_release_publish.py::test_publish_without_authorization_reports_artifacts` builds the same repo with no `release` block and no token in env. `main(["publish"], ...)` returns 0, makes no `uv publish` call, and prints the two `publish: built` lines and the `uploaded nothing` line. Both printed paths exist under `<state_dir>/dist`. Ruled out: uploading under the default config.
11. `tests/integration/test_release_publish.py::test_publish_refusals_change_nothing` covers three repos built as in criterion 9:
    - one where a further commit follows the tag;
    - one with no tag;
    - one where the test holds `Lockfile(state_dir, ...)` itself.
    Each `main(["publish"], ...)` returns 2 with stderr starting `clutch publish:`. The first two name `v0.4.0` and `clutch release` and make no `uv build` or `uv publish` call. The held-lock case names `clutch.lock` and makes no `uv` call. HEAD and the tag list are unchanged in all three. Ruled out: a build or upload reached before a refusal.
12. `tests/integration/test_release_publish.py::test_release_journals_the_release_signal` uses the `repository` fixture of `tests/integration/test_release.py`. After `main(["release", "--minor"], cwd=repo, env=ENV)` returns 0, `Journal(<state_dir>, clock).read()` holds exactly one `signal` event, whose body is `{"signal": "release", "version": "0.2.0", "tag": "v0.2.0", "commit": <HEAD sha>}`. Ruled out: a missing signal, and a signal naming a commit other than the tagged one.
13. `tests/integration/test_release_publish.py::test_dev_publish_is_removed` sets `dev.sys.argv` to `["dev.py", "publish"]`. `dev.main()` raises `SystemExit` with code 2, and the faked `dev.subprocess.run` is never called. Ruled out: a surviving `./dev.py publish` that bumps or uploads.
14. `./dev.py test tests/unit/test_host_running.py tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py tests/integration/test_host_contract.py tests/integration/test_dev.py` exits 0, with the `publish` verb row, `"release"` in `SIGNAL_NAMES` written by engine code, and the `Release` inventory rows in place. The docs command in `## Verification` also exits 0. It checks these docs:
    - the `publish` row and the "Stop serve before" mention in `clutch/docs/host-running.md`;
    - a `publish` row in `docs/how-clutch-works.md` section 2.1 and none in section 2.2;
    - a `dist/` row in section 10.1;
    - a `release` row in section 11;
    - no `publish` in the `CLAUDE.md` Command surface bullet;
    - no `"publish"` in `dev.py`.
15. The unit check (`clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`) passes. `clutch/release.py` is at or above `test-gate.toml`'s `default = 90`, and `clutch/redact.py`, `clutch/config.py`, `clutch/providers.py`, `clutch/journal.py`, and `clutch/__main__.py` are at or above their `[coverage.files]` floors.
16. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_release_publish.py tests/unit/test_release.py tests/unit/test_host_running.py tests/unit/test_preflight_parallel.py tests/unit/test_probe_verb.py tests/unit/test_qwen_adapter.py tests/unit/test_update_config_verb.py
./dev.py test tests/integration/test_release_publish.py tests/integration/test_release.py tests/integration/test_dev.py tests/integration/test_closed_sets.py tests/integration/test_vocabularies.py tests/integration/test_host_contract.py
uv run python -c "import pathlib; q = chr(96); h = pathlib.Path('clutch/docs/host-running.md').read_text(); assert '| ' + q + 'publish' + q + ' | No |' in h; stop = next(line for line in h.splitlines() if line.startswith('Stop serve before')); assert q + 'publish' + q in stop; w = pathlib.Path('docs/how-clutch-works.md').read_text(); verbs = w.split('### 2.1 Verbs')[1].split('### 2.2')[0]; dev = w.split('### 2.2')[1].split('## 3. Tickets')[0]; config = w.split('## 11. Config')[1].split('## 12.')[0]; files = w.split('### 10.1 Files')[1].split('### 10.2')[0]; assert '| ' + q + 'dist/' + q + ' |' in files; assert '| ' + q + 'publish' + q + ' |' in verbs; assert '| ' + q + 'publish' + q + ' |' not in dev; assert '| ' + q + 'release' + q + ' |' in config; rule = next(line for line in pathlib.Path('CLAUDE.md').read_text().splitlines() if line.startswith('- **Command surface.**')); assert q + 'publish' + q not in rule; assert chr(34) + 'publish' + chr(34) not in pathlib.Path('dev.py').read_text()"
./dev.py test
```

## Definition of rejected
The branch is rejected if any of these holds:
- `clutch publish` bumps the version, commits, tags, or pushes;
- it uploads when `release.publish` is absent or false;
- it uploads a version whose `v<version>` tag is missing or not on HEAD, or builds over uncommitted tracked changes;
- the token value reaches any child process other than the `uv publish` upload, appears in an argv, or reaches the upload under any env var name other than `UV_PUBLISH_TOKEN`;
- `release.publish` defaults to true;
- `./dev.py publish` survives, or any `dev.py` subcommand is added;
- it adds `release.vsce_token`, `vsce publish`, or any Marketplace upload;
- it adds a `publish` journal signal, a park, or a `confirm` path;
- `clutch/release.py::release` changes beyond the `main` branch journaling its signal;
- it adds an extension surface, a `clutch/help.py` entry, or a `vscode-clutchwork/` change.

## Time budget
- expected: 90m
- stuck: 180m
