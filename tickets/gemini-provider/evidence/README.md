# Gemini CLI A0 hand test: evidence

An agent ran this on 2026-11-15 (UTC 2026-11-16) with `@google/gemini-cli` 0.49.0, as `docs/gemini-graphics-refactor-plan.md` Part A "Prerequisite: hand test (A0)" requires. Auth was a paid-tier `GEMINI_API_KEY`. Every call ran through `bash -ic` (the key exists only in interactive shells), with `HOME` set to a fresh scratch directory and the working directory in scratch. `<scratch>` in the fact files stands for `/tmp/claude-1000/-home-djp-source-clutch/29e87c0b-6495-4286-9d98-811e7abc64d3/scratchpad/gemini-a0`.

Each `fact-NN-*.txt` file holds the finding, then every supporting run: argv, env overrides, cwd, stdin, exit code, stdout, and stderr. Stack frames are dropped from stderr. Facts 01-09 are the plan's nine facts. Facts 10-14 are the facts the digest and caller added. Spend was about 330k tokens plus 4 generated images, roughly USD 0.30-0.40 (an estimate, because the CLI reports no cost).

## Facts

1. **Result event shape** (`fact-01`). `-o stream-json` emits JSONL events: `init` (`session_id`, `model`), `message` (user echo, then assistant `delta` chunks), `tool_use`/`tool_result` (paired by `tool_id`), `error`, and a terminal `result` with `status` `success`|`error`, an optional `error{type,message}`, and `stats` (token counts plus a `models` map). The reply text is the concatenation of the assistant chunks. `result` carries no text. `-o json` prints one object `{session_id, response, stats}`. On failure that object is `{session_id, error}` on stderr and stdout is empty.
2. **Failed-turn exit** (`fact-02`). Failures can exit 0. An "Invalid stream" turn (an image-only reply, or a malformed or empty response) gives `result.status: "error"` with exit 0, and a refusal is `success` with exit 0. Other observed codes: 1 (model 404), 144 (invalid key: HTTP 400 mod 256), 41 (no auth), 42 (no input), and 55 (untrusted dir). The parser must key on `result.status`. On API errors the real reason is often only on stderr, because `result.error.message` reads "[API Error: An unknown error occurred.]".
3. **Read-only and write grant** (`fact-03`). A `tools.core` read-only allowlist in the `GEMINI_CLI_SYSTEM_SETTINGS_PATH` file blocks writes and shell even under `--approval-mode yolo`, and a workspace `.gemini/settings.json` cannot widen it. A system file without `tools.core`, plus `--approval-mode yolo`, writes and runs shell. `plan` and headless `default` are also read-only for the worktree. Plan mode may write plan files under `~/.gemini/tmp`. `auto_edit` writes but has no shell. The full tool set includes an `invoke_agent` subagent whose tool calls are invisible in the stream.
4. **context.fileName** (`fact-04`). `context.fileName: "AGENTS.md"` loads `AGENTS.md`, but it adds to `GEMINI.md` rather than replacing it, so a host's `GEMINI.md` still loads.
5. **Auth and quota wording** (`fact-05`). Observed: "Please set an Auth method ..." (exit 41), "API key not valid ... API_KEY_INVALID" (exit 144), and "ModelNotFoundError ... no longer available". Quota wording comes from source only: `RESOURCE_EXHAUSTED`, "You have exhausted your daily quota on this model.", and "... request a quota increase through AI Studio ...".
6. **Process argv** (`fact-06`). Each call runs two node processes: the launcher and a `--max-old-space-size` relaunch child. Under pnpm, argv[1] is `.../@google/gemini-cli/bundle/gemini.js`. Under npm/nvm (this machine), it is `.../bin/gemini`, which the plan's `@google/gemini-cli` matcher misses.
7. **Image generation headless** (`fact-07`). Negative. The image model rejects the CLI's tool declarations ("Function calling is not enabled") and its thinking config. With `tools.core: []` and a custom model alias it does generate, including from 2 or 4 `@path` input images, but the CLI discards the image: nothing reaches stdout, a file, or the session record. Image-only replies are even reported as "Invalid stream" errors (exit 0). The bytes could be recovered only by scraping a telemetry debug log (`fact-07-generated-*.png`).
   **`api-provider-client` (roadmap row 56) is needed.** The CLI cannot write a generated image to a file, so the trigger in `CLUTCH_PLAN.md` §18.2 has fired.
8. **Judge call** (`fact-08`). Positive. Three `@path` images plus a rubric to `gemini-3.1-pro-preview` returned schema-shaped JSON headless, with correct verdicts. Temperature 0 and a JSON schema cannot be set from argv. They are set through `modelConfigs.customAliases` in the system settings file (`responseMimeType`, `responseJsonSchema`, `temperature: 0`; the alias needs `extends: chat-base-3`), and telemetry confirmed they were sent.
9. **Python 3.14 wheels** (`fact-09`). Positive. With `--only-binary :all:`, all `images` and `images-embed` packages resolve for CPython 3.14 on Linux x86_64, macOS arm64, and Windows x86_64. On macOS, torch stops at 2.11.0. On Linux, torch pulls about 20 CUDA packages.
10. **Prompt delivery** (`fact-10`). `-p` is not required: with non-TTY stdin and stdout, a stdin-only prompt runs headless, and stdin plus `-p` joins as `stdin\n\n-p`. stdin is capped at 8 MiB. Stdin must start arriving within 500 ms, or the CLI exits 42 "No input". A `-p` argument over 128 KiB fails at exec.
11. **Workspace trust and files** (`fact-11`). Headless in an untrusted dir exits 55. `--skip-trust`, `GEMINI_CLI_TRUST_WORKSPACE=true`, and `security.folderTrust.enabled: false` in the system settings file all pass. The CLI writes only under `~/.gemini`: `installation_id`, `projects.json`, and per-project `tmp/<name>/chats/session-*.jsonl` full transcripts. API errors also write `/tmp/gemini-client-error-*.json`. Nothing is written in the working directory.
12. **Model selection** (`fact-12`). `-m` is not a literal pin. Any name ending in `flash` (for example `gemini-2.5-flash` or `gemini-3.8-flash`) is rewritten to `gemini-3.5-flash` and served as `gemini-3.6-flash`. Unknown names pass through. `init.model`, the session record, and `stats.models` can show three different names, and the `stats.models` key is the model actually served.
13. **Session id and cost** (`fact-13`). The session id appears in `init.session_id` and json `session_id`, and `--session-id <uuid>` is honored. No USD cost appears anywhere, only tokens. Each call carries about 8k input tokens of CLI system prompt.
14. **list_models** (`fact-14`). The CLI has no model-listing command, and its built-in table omits the image models. API ListModels lists 64 models but is not authoritative: `gemini-2.5-pro` is listed yet returns 404. The owner-note names `gemini-3-pro` and `gemini-3-flash` are not served ids.

## Plan assumptions these facts make false

- **Argv.** `gemini -m <model> --output-format stream-json` with stdin fails with exit 55 unless it carries a trust grant. Fold `security.folderTrust.enabled: false` into both packaged settings files, or add `--skip-trust`.
- **Model pinning.** `-m` does not pin flash-family models (fact 12).
- **Parsing.** It must not trust exit 0 (fact 2).
- **Conduct file.** `context.fileName` cannot exclude `GEMINI.md` (fact 4).
- **Live-call matcher.** The `live_call` matcher misses npm installs (fact 6).
- **Image generation (B1, B6).** Image mode via the CLI is impossible (fact 7).
- **Judge temperature (B5).** "Temperature 0 where the CLI allows it" works only through a settings-file model alias (fact 8).
- **Input cap (B1).** The input-image cap "3, the smallest" is not enforced: 4 worked (fact 7).
- **Owner-note models.** The judge names `gemini-3-pro`, `gemini-3-flash`, and `gemini-2.5-pro` are not usable with this key (fact 14).

## Files

- `fact-01-result-event-shape.txt` to `fact-14-list-models.txt`
- `fact-07-generated-fusion.png`: the 1024x1024 output fused from the 2 input images, recovered from telemetry
- `fact-07-generated-4-inputs.png`: the 1024x1024 output from 4 inputs, which the CLI reported as an error
- `fact-07-input-red-circle.png`, `fact-07-input-blue-square.png`: the 64x64 inputs
