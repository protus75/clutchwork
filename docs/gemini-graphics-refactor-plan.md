# Gemini provider and graphics ticket kind: refactor plan

Add Google's Gemini CLI as a fourth provider beside `claude`, `codex`, and `qwen` (Ollama), and add a `graphics` ticket kind for two kinds of visual work: output that code renders (web pages, SVG, flowcharts, charts) and images an image model generates or edits. The Gemini provider exists for the second kind: its image models take several input images in one prompt and return an image, which no other routed CLI does. Graphics tickets are graded in three layers: deterministic checks with no model, a vision-model judge on a rubric, and best-of-N selection where only cases the judge is unsure about park.

## Status

The Gemini provider, including `GeminiAdapter` in `clutch/providers.py`, has merged (roadmap row 32). The graphics ticket kind and visual review remain planned (rows 49–55). Written 2026-11-13 at commit `c7f8d6c1`; revised 2026-11-13 at commit `80b76d5d` for `docs/roadmap.md`; revised 2026-11-14 at commit `009c211d` after the owner decided Part B's scope, routing, sign-off, grading, and dependencies (`docs/roadmap.md` §6, decisions 15-18).

## Roadmap

Part A (`gemini-provider`) is release 0.3.0 (`docs/roadmap.md` row 32); it needs nothing and waits on its agent capture. Part B is release 0.4.0 (rows 49-55): seven tickets, depending on `closed-sets-single-owner` (row 19), which gives the kind set one home before this plan adds a member to it. What needs this plan: `evidence-normalize-gemini` (`docs/evidence-trail-plan.md` ticket 5) waits on `gemini-provider` and uses the A0 agent capture as its fixture. Shared files: `graphics-render-check` and the parallel plan's `conflict-discard-rerun` both bump `clutch/specs/implement.md`; this plan's ticket runs first (roadmap decision 8). Render commands run through `run_host_command`, under the parallel plan's host-command lock (decision 10). The judge's `graphics.judge_samples` majority is the `majority-verdict` combiner of `docs/stage-panels-plan.md` (decision 14); B5 moves onto it when that plan lands in 0.5.0 and until then carries its own per-row majority. Shared budget: `graphics-kind` adds 9 bytes (`|graphics`) to CORE_TEMPLATE (decision 5). New dependencies ship as optional extras (decision 18), never in core.

**Risk the agent capture must retire first.** Part B's image mode assumes Gemini CLI can call an image model headlessly and write the result to a file. If A0 shows it cannot, image generation needs the `kind: api` provider client that `CLUTCH_PLAN.md` §18.2 defers to "the first configured `kind: api` provider". That trigger would then have fired, and an `api-provider-client` ticket (image models only, no new surfaces) joins 0.4.0 ahead of `image-candidates-select`. The plan is written for the CLI case; the api case changes only where the image call is made, not the grading.

## Part A: Gemini CLI provider

### Current state

- `ADAPTERS` in `clutch/providers.py:544` ships `claude`, `codex`, and `qwen`. A provider named `gemini` is refused at setup: `no shipped cli adapter` (`providers.py:579`).
- `QwenAdapter` subclasses `ClaudeAdapter` (`providers.py:514`) because Qwen Code emits Claude's stream format. Qwen Code is a fork of Gemini CLI, but Gemini CLI's own `stream-json` is a different format, so Gemini cannot reuse `ClaudeAdapter.parse`.
- `clutch/watchdog.py` reads two event shapes: Claude's (`assistant` `tool_use` blocks, which qwen shares; line 92) and Codex's (`item.*`; line 99). It has no Gemini branch.
- `clutch/observe.py` `live_call` (189-215) labels claude, codex, and qwen processes only.

### Config: no schema change for the provider

`Provider` in `clutch/config.py:72-84` already carries every field Gemini needs:

| Field | Gemini value |
|---|---|
| `kind` | `cli` |
| `package` | `@google/gemini-cli` (the preflight's latest-release check works unchanged) |
| `auth` | unset for a Google OAuth login (ambient, like claude and codex), or `GEMINI_API_KEY` for a key. `child_env` (`providers.py:78`) already passes a key only to its own provider. |
| `base_url` | unset (refused, since `uses_base_url` stays false) |
| `models_by_tier` | `OPERATOR-SETS-THIS` until the operator picks models; the placeholder refusal already covers this |
| `limits.est_cost_per_call_usd` | required: the stream reports tokens, never USD |

Config support is therefore a setup guide plus a routing example. Routing Gemini in this repo's `config.yaml` is a ticket’s change after setup. The one routing schema change this plan makes (`Route.kinds`, Part B3) serves graphics tickets, not the provider.

Example declaration for the guide:

```yaml
- name: gemini
  kind: cli
  package: "@google/gemini-cli"
  models_by_tier: {low: OPERATOR-SETS-THIS, medium: OPERATOR-SETS-THIS, high: OPERATOR-SETS-THIS, max: OPERATOR-SETS-THIS}
  limits: {concurrency: 1, est_cost_per_call_usd: 0.50}
```

Out of scope: Vertex AI auth, which needs several env vars (`GOOGLE_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI`, project, location) while `auth` names one.

### Owner-supplied model notes (2026-11-14; A0 confirms them)

- The image models (`gemini-2.5-flash-image`, `gemini-3-pro-image-preview`, `gemini-3.1-flash-image-preview`) accept several images in one prompt (3, 14, and 10 inputs respectively), and are built to fuse, restyle, or edit those inputs and return an image. "Put the product from image A into the scene from image B" works well; "draw image A with the differences from image B circled" works roughly, not at pixel precision.
- A textual comparison ("what changed between these two screenshots", "which of these matches the spec") is an analysis task. The image models can emit text but are tuned to answer with a picture. The general multimodal models (`gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-3-pro`, `gemini-3-flash`) take multiple images and return text, and reason about differences far better.
- For an exact diff, neither is the right tool: use a pixel or perceptual-hash comparison, and send the result to a model only for a natural-language explanation.

These three facts fix the roles in Part B: an image model generates (Implement), a general multimodal model judges (`review_visual`), and mechanical code diffs (the `image_quality` gate).

### Target design

- **`GeminiAdapter(CliAdapter)`** with its own `argv` and `parse`: it sets `PACKAGE = "@google/gemini-cli"`, required by `clutch install gemini` and the closed-set pin.
  - argv: `gemini -m <model> --output-format stream-json` plus the write grant; the prompt arrives on stdin, as for every adapter.
  - parse: read the `stream-json` events (`init`, `message`, `tool_use`, `tool_result`, `error`, `result`). The terminal `result` event carries the outcome and token stats. Raise `ValueError` when there is no successful `result`.
  - `reports_cost = False`, `AUTH_MARKERS`, and a `LOGIN_ROAD` naming `clutch/docs/host-gemini.md` and `clutch drain`.
- **Write grant, fail closed.** Ship two settings files in the package and select one per call through `GEMINI_CLI_SYSTEM_SETTINGS_PATH`, the same mechanism `qwen-settings.json` uses through `QWEN_CODE_SYSTEM_SETTINGS_PATH` (`providers.py:541`):
  - `gemini-readonly.json`: a `tools.core` allowlist of the read tools only (read file, glob, search, list directory), matching Claude's `--tools Read Grep Glob LS`.
  - `gemini-write.json`: full tools, with `--approval-mode yolo` on the argv.
  - Both set `context.fileName` to `AGENTS.md`.
  - System settings are the top-precedence layer, so nothing in `~/.gemini/settings.json` or a workspace `.gemini/settings.json` can widen the grant or move the conduct file. The operator never edits a file in their home directory.
- **Conduct file.** Gemini reads `AGENTS.md`, the curated subset for non-Claude CLIs. `routed_conduct_paths` (`providers.py:128-132`) already selects `AGENTS.md` for any provider not named `claude` or `qwen`, so no code change; add a test.
- **Failure classes.** Extend `FAILURE_MARKERS` (`providers.py:37`) with Gemini's quota and rate wording (for example `RESOURCE_EXHAUSTED`, `quota exceeded`, 429). It is a shared allowlist, so the additions must not misclassify claude or codex output; the existing classifier tests cover that.
- **Watchdog.** A third branch in `clutch/watchdog.py` for Gemini's `tool_use` and `tool_result` ids and `result` stats, so stall detection and token metering work. (`docs/evidence-trail-plan.md` later moves all three branches onto the normalizers; roadmap decision 13.)
- **Live view.** A `live_call` branch for the pnpm shim's `node .../@google/gemini-cli/...` process, labelled `gemini <model>`.
- **Guide.** New `clutch/docs/host-gemini.md`: what it is, install (`pnpm add -g @google/gemini-cli@latest`), log in or export `GEMINI_API_KEY`, declare it, `clutch probe gemini`, route it, limits (free-tier rate limits, `quota_window_minutes`), and which models generate images and which judge them. The `docs` verb lists it as a fifth guide.

### Prerequisite: agent capture (A0)

The qwen ticket was decidable because a run with an empty `HOME` established its facts before authoring (rule: read before write). An agent captures the nine facts and commits them under `tickets/gemini-provider/evidence/`, also the normalizer's golden fixture. For facts 1-8, run headless `gemini` per settings file with an empty `HOME`, saving stdout, stderr, exit code and live process argv; this needs the Gemini credential. For fact 9, resolve the `images` and `images-embed` extras on Python 3.14 in a scratch venv and save resolver output; this needs no credential. Until a Gemini credential exists, `gemini-provider` and dependent rows are skipped while an agent looks for a route to image generation and judging through the authenticated providers (`docs/roadmap.md` §6, decision 19). Establish:

1. The exact `result` event shape for success and failure, and where the reply text and token counts live.
2. The exit code of a failed turn, and whether a failure can exit 0 (codex does).
3. Whether a `tools.core` allowlist in the system settings file actually blocks writes and shell under headless mode, or whether `--approval-mode plan` (or default approval) is the read-only mode.
4. That `context.fileName` from the system settings file loads `AGENTS.md` from the working directory.
5. The auth-failure and quota wording on stderr or in `error` events.
6. The process argv the pnpm shim produces, for `live_call`.
7. **Image generation headless:** whether `gemini -m gemini-2.5-flash-image` (or a tool the CLI exposes) can take input image paths and a prompt on stdin and write an output image file, non-interactively; the output's format and location; input-image limits as observed. If it cannot, Part B's image mode needs the `kind: api` client (see Roadmap).
8. **Judge call:** whether the CLI can send several images plus a prompt to a general multimodal model and return text constrained to a JSON schema, and whether temperature can be set to 0 from the argv or settings.
9. Wheel availability on Python 3.14 (the project floor) for the `images` extras: Pillow, numpy, scikit-image, imagehash, opencv-python-headless, and for `images-embed`: open_clip and torch.

No argv or parse in this plan is final until that capture is committed.

### Fence (ticket `gemini-provider`)

- `clutch/providers.py`
- `clutch/gemini-readonly.json` (new)
- `clutch/gemini-write.json` (new)
- `clutch/watchdog.py`
- `clutch/observe.py`
- `clutch/__main__.py` (docs verb tuple)
- `clutch/docs/host-gemini.md` (new)
- `clutch/docs/host-contract.md` (shipped adapter list, no-cost rule, conduct-file sentence)
- `docs/how-clutch-works.md` §8.1
- `README.md` (only if it lists the CLIs)
- `tests/unit/test_gemini_adapter.py` (new)
- `tests/unit/test_live_call.py`
- `tests/unit/test_docs_verb.py`
- `tests/integration/test_cli.py`
- `tests/integration/test_closed_sets.py` (`ADAPTERS`, line 242)
- `tests/integration/test_watchdog.py` and `tests/integration/test_watchdog_activation.py` (the watchdog has no unit test file; the new branch's tests go in a new `tests/unit/test_watchdog_gemini.py`)

## Part B: `graphics` ticket kind

### Current state

- `kind` is the closed set `feature | bug | chore` (`clutch/tickets.py:59`). It is repeated in:
  - `clutch/__main__.py`: `--kind` choices (line 269) and the kind check in `_new` (line 791 at `80b76d5d`);
  - `clutch/stats.py:108`;
  - `clutch/author.py:245` (skeletons embedded in the Author prompt);
  - `tests/integration/test_closed_sets.py:342`;
  - the `CORE_TEMPLATE` rule text in `clutch/hostfiles.py` (`clutch new <stem> --kind feature|bug|chore`), and through `clutch core` the managed blocks in `CLAUDE.md` and `AGENTS.md`.

  `closed-sets-single-owner` (roadmap row 19, 0.3.0) collapses the code copies to `Frontmatter` in `tickets.py` with argparse deriving its choices; B1 depends on it so that adding `graphics` is one edit plus the template.
- `bug` is the precedent for a kind with its own machinery: an extra section (`## Regression`), a stdout protocol (`regression_result`), committed evidence files, and a Check rule that runs the command at head and at base.
- `## Context` accepts only UTF-8 text (`tickets.py:396`), so mockups, reference images, and input images have no place in a ticket today.
- Review is text-only: it sees `git diff main...<stem>`, where an image is `Binary files differ`. Nothing renders the output or looks at it.
- `host-authoring.md` requires every criterion to be "a check someone can run or a path someone can read, never a judgment word". Visual work has criteria that only an image can decide.
- `review.mechanical` already accepts a path-prefix `trigger` (`config.py:99,105,108`), so a host can run a Markdown or Mermaid check on changed files today.
- `Route` (`config.py:99-102`) is `tier`, `surface`, `candidates`; `resolve()` (`providers.py:101-108`) picks by `(tier, surface)` with a fallback to the `review` row. Nothing routes by ticket kind.
- clutch has no image or ML dependency.

### Scope of "graphics"

One kind, two modes, declared in `## Render`:

- **`mode: command`** — output rendered from code the agent writes: HTML/CSS pages, UI components, SVG, Mermaid or Graphviz flowcharts, matplotlib-style charts. The host owns the renderer.
- **`mode: generate`** — images an image model generates or edits from a prompt and up to N input images: product shots composed into scenes, restyled assets, illustrations. The implementer is the image model, routed by kind (B3).

Both modes share the criteria forms, the visual review, and the sign-off rule. The grading layers (B4-B6) are built for `generate` and apply to `command` where they make sense (layer 1's existence and format checks always; preservation and presence only when the ticket names a base or input image).

### Target design

#### B1. Grammar and authoring (`graphics-kind`)

- `kind` gains `graphics`, with its own template.
- New section `## Render`, required on `graphics` and refused on every other kind, like `## Regression`:

  ````
  ## Render
  - mode: generate
  - artifact: assets/hero.png
  - input: tickets/<stem>/reference/product.png
  - input: tickets/<stem>/reference/scene.png
  - reference: tickets/<stem>/reference/hero-mock.png
  - candidates: 3
  ````

  For `mode: command` the block instead carries the fenced render command, `artifact:` paths under a gitignored render directory, optional `reference:` paths, and `carries:` (the command must name a path under a carried prefix, which must be fenced):

  ````
  ## Render
  ```
  uv run python tests/render/home.py
  ```
  - mode: command
  - artifact: .clutch/renders/home.png
  - reference: tickets/<stem>/reference/home-mock.png
  - carries: tests/render
  ````

  - `artifact:` names each output. In `generate` mode the artifact is a committed repo path (the image is the deliverable); in `command` mode it lives under a gitignored render directory and is never committed.
  - `input:` names the images the generator receives (`generate` only), committed under `tickets/<stem>/reference/`. Lint caps the count at the routed model's limit once A0 records it; until then at 3, the smallest.
  - `reference:` names optional mockups or baselines, committed under `tickets/<stem>/reference/`.
  - `candidates:` (`generate` only) is the best-of-N count, 1 to 5, default 3.
- `clutch new <stem> --kind graphics [--reference FILE...] [--input FILE...]` copies the files the way `--evidence` copies bug evidence. Intake commits them with the ticket.
- Acceptance criteria come in two forms:
  - Mechanical criteria, checked by tests or by the layer-1 gate: text present, DOM selector exists, image dimensions, the Mermaid source parses, a contrast ratio, an SSIM floor against a base image, a keypoint-match floor for an input image.
  - Visual criteria, written `- visual: <artifact>: <observable>`. The observable is something you can see and answer yes or no: an element, a label, a position relative to another element, a colour token, "the product from `product.png` sits on the table at the left third". Never "looks clean" or "modern".
  - Lint enforces the structure (each `visual:` criterion names a declared artifact; a graphics ticket has at least one mechanical criterion; `generate` mode names at least one `input:` or a prompt in `Goal / Why`). The LLM requisition review checks that each visual criterion can be decided from the image alone. A lint rule cannot judge that, and a denylist of judgment words breaks the fail-closed rule.
- `clutch/docs/host-authoring.md` gains a **Graphics tickets** section, beside **Bug tickets**, covering both modes, the render block, artifacts, inputs and references, the two criterion forms, the grading layers and which undecided cases park, preferring a mechanical criterion wherever a test can decide it, and the Markdown and flowchart checks hosts declare in config.

#### B2. Check for `mode: command` (`graphics-render-check`)

- Check runs the render command at the branch head through `stages.run_host_command`, so it is spooled like a Verification command and, once `docs/parallel-tickets-plan.md` ships, runs under the one host-command lock. It prints exactly one JSON object, `{"render_result": "ok", "artifacts": [...]}`, and exits 0. Like `regression_result`, any other stdout, extra keys, or a disagreeing exit code is refused. `{"render_result": "error"}` means a missing prerequisite and never counts as success.
- The engine checks that the listed artifacts are exactly the declared ones, each exists, is non-empty, and has content matching its extension (PNG header, SVG/XML root, HTML).
- The artifacts are copied into the attempt directory (`tickets/<stem>/attempts/<n>/render/`) so the visual reviewer and the operator can open them.
- The host owns the renderer: a Playwright screenshot script, `mmdc` for Mermaid, `dot` for Graphviz. The engine runs only the command, which keeps it free of a browser dependency.
- Markdown and flowchart checking needs no engine change. A host declares it in `config.yaml`, for example:

  ```yaml
  - {code: mermaid, argv: [npx, mmdc, --validate], trigger: ["*.md", "*.mmd"], severity: hard}
  - {code: markdownlint, argv: [npx, markdownlint-cli2], trigger: ["*.md"], severity: soft}
  ```

  The guide documents this. Validate the exact argv when the guide is written.

#### B3. Routing by ticket kind (`route-kinds-filter`)

Decided 2026-11-14: build it now, not after a failure.

- `Route` gains an optional `kinds: list[Kind]` (absent means every kind). `resolve()` takes the ticket's kind and picks, in order: a `(tier, surface)` row whose `kinds` names the kind; a `(tier, surface)` row with no `kinds`; the `(tier, review)` fallback with the same two steps. A row with `kinds` never serves a kind it does not name.
- This is a config schema change: the strict loader on an older clutch refuses a config carrying `kinds` as an unknown key, which `clutch/docs/host-contract.md` "Version migration" already describes as the behavior for a newer config ("Newer versions refuse with a road to upgrade clutch"). `schema_version` stays 1 because the key is optional and additive; the contract's inventory gains the field.
- Example for this repo once its models are set:

  ```yaml
  - {tier: medium, surface: implement, kinds: [graphics], candidates: [{provider: gemini, model: gemini-3.1-flash-image-preview}]}
  - {tier: medium, surface: review_visual, candidates: [{provider: gemini, model: gemini-3-pro}]}
  ```

- **Judge independence.** `doctor` warns, and `clutch lint` on a graphics ticket snags, when the `review_visual` route resolves to the same model family as the graphics `implement` route (same provider and the same model, or an image model for the judge). The owner's note is the rule: the judge must be a general multimodal model, from a different family where possible, never the image model that produced the candidate.

#### B4. Layer 1: deterministic checks (`image-quality-gate`)

A new engine gate code `image_quality`, implemented in `clutch/images.py`, run by Check on every declared artifact in both modes. No model call. Fail closed: a check the ticket enables and the engine cannot run is a hard failure with a paved road, never a skip.

| Check | What it decides | Needs |
|---|---|---|
| exists, decodes, dimensions, aspect ratio | the artifact is an image of the declared size | Pillow |
| not blank | pixel variance above a floor | numpy |
| not a copy of an input | perceptual-hash distance from every `input:` above a floor | imagehash |
| preservation | SSIM at reduced resolution against the base image (`input:` marked `base`), masking the region where the insert was supposed to land; a threshold, not equality, because the model regenerates the whole frame | scikit-image |
| presence | ORB (default) or SIFT keypoint matches between an `input:` and the output, or when the ticket asks for `presence: embedding`, CLIP/DINO similarity between the input and the crop at the expected location; a score near zero means the input was ignored | OpenCV; `open_clip` for embedding |

- Thresholds are per-check engine defaults that a ticket may tighten, never loosen, in its mechanical criteria (`- ssim: >= 0.85 outside region (x, y, w, h)`). The defaults are set by the calibration in B7.
- The gate also writes the operator artifacts the later layers show: a side-by-side of inputs, reference, and candidate, and a diff heatmap against the base image, under `tickets/<stem>/attempts/<n>/render/`.
- **Dependencies ship as extras** (decision 18): `clutch[images]` = Pillow, numpy, scikit-image, imagehash, opencv-python-headless; `clutch[images-embed]` = open_clip and torch, for the embedding presence check only. `clutch/images.py` imports them lazily. A graphics ticket on a host without the extra fails the gate with the road `uv add --dev "clutch[images]"` (or `images-embed` when the ticket asks for embedding presence). Core clutch gains no dependency.

#### B5. Layer 2: the vision-model judge (`visual-review-surface`)

- New spec `clutch/specs/review_visual.md` and surface `review_visual`. It runs after the correctness review, on `graphics` tickets only, read-only, routed by B3 to a general multimodal model that is not the generator.
- Inputs: the ticket, the prompt the generator received, every `input:` and `reference:` image, each candidate artifact, and the layer-1 scores. The reviewer opens images with its read tool (Claude's Read and Gemini's file reader both take images).
- Rubric: the ticket's `visual:` criteria, plus for `generate` mode five fixed rows: the input is present and recognisable with the same identity and proportions; it is at the requested position and scale; lighting, shadows, and perspective match the base; everything outside the insert region is unchanged; no artifacts (warped text, extra limbs, seams, duplicated objects).
- Output: structured JSON under a schema the gate enforces: one `pass` / `fail` / `unsure` per rubric row with the observation that decided it, and an overall verdict `accept` / `reject` / `unsure` with one sentence of reason. A reply that skips a row or names one not in the rubric is refused and re-prompted, as every driver reply is.
- Temperature 0 where the CLI allows it (A0 fact 8). `graphics.judge_samples` (config, 1 to 3, default 1) runs the judge that many times on independent calls and takes the per-row majority; ties are `unsure`.
- Every judge call is an ordinary driver call, so it gets the evidence record and counts against spend like any other.

#### B6. Layer 3: candidates, selection, and the undecided park (`image-candidates-select`)

- For `mode: generate`, Implement produces `candidates:` images into `tickets/<stem>/attempts/<n>/render/cand-<k>.<ext>` (uncommitted) rather than the artifact path. The `implement.md` graphics block says so and forbids committing a candidate directly.
- Check runs layer 1 on every candidate and drops any that fails a hard check. The judge (B5) scores the survivors. Ranking: judge verdict, then the count of `pass` rows, then the layer-1 presence and preservation scores.
- **Select commit.** The top candidate with verdict `accept` and a margin (at least one more `pass` row than the runner-up, or the only survivor) is copied to the artifact path and committed as `clutch(<stem>): select`, the way Check already commits autofix changes. Review (correctness) then sees the committed image in the diff; the visual judgment is already on record.
- **Park.** No `accept`, an `accept` without margin, or any `unsure` overall verdict parks the ticket with reason `visual_undecided` and the side-by-side and heatmap artifacts for each surviving candidate. No person releases it (`docs/roadmap.md` §6, decision 19); open decision 4 settles what does, and `image-candidates-select` builds that release.
- Decided 2026-11-14: the judge decides; only the undecidable parks. There is no always-hold.

#### B7. Calibration before trust (`visual-review-baseline`)

The thresholds in B4 and the rubric wording in B5 are guesses until measured. Following the review-baseline precedent (`eval/harness.py`, `docs/how-clutch-works.md` §9.6):

- `eval/visual/` holds 20 to 50 outputs, each labelled `accept` or `reject` by an AI label panel whose members are all from a model family other than the judge's (`docs/roadmap.md` §5, decision 13), with inputs and prompts committed as fixtures.
- `./dev.py visual-baseline` reports the judge's agreement with the panel's labels per rubric row and overall, and the layer-1 score distributions that separate the labels. The report is committed like the review baseline's.
- The `visual_baseline` verdict, bound to the judge's provider, model and `review_visual.md` version, is GO at 0.85 or above overall agreement and NO_GO below: the review baseline's catch floor (`eval/harness.py`, `MIN_CATCH_RATE`). No person approves it. Until GO, every graphics ticket parks at B6 and the label panel's verdicts on parked candidates grow the fixture set.
- Tighten the rubric wording and layer-1 defaults until agreement reaches 0.85.

#### B8. Spec updates

- `clutch/specs/implement.md`: a graphics block. For `command` mode: run the render command, open your own artifacts, compare them with the references and the visual criteria before committing; never commit artifacts. For `generate` mode: produce the declared number of candidates from the inputs and prompt; never commit a candidate; name in `run.md` what varied between candidates. The parallel plan's `conflict-discard-rerun` also bumps this spec; B2 runs first, and that ticket takes the next minor above what B2 leaves.
- `clutch/specs/requisition_review.md`: a graphics block. Each `visual:` criterion can be decided from the named artifact alone. Snag a criterion that needs taste or a reading of intent, a `generate` ticket with no input and no prompt, and a `review_visual` route that resolves to the generator's model.
- `clutch/specs/review.md`: for graphics tickets, the correctness reviewer judges the code and the committed artifact's provenance (the select commit matches a graded candidate), not the picture; the picture is `review_visual`'s.
- `clutch/specs/author.md`: no text change. It embeds the skeletons, which gain `graphics` through `author.py`.
- Every bumped spec takes the next minor version above its version on main, and its test pin is fenced.

### Where each rule lives

| Rule | Home |
|---|---|
| What a graphics ticket contains, both modes, how criteria are written, what parks | `clutch/docs/host-authoring.md` (the one authoring source) |
| Ticket format (`## Render`, bullets, kind) | `clutch/tickets.py` |
| Routing by kind, judge independence | `clutch/config.py` (`Route.kinds`), `clutch/providers.py` (`resolve`), `clutch/doctor.py` |
| Layer 1 checks, thresholds, operator artifacts | `clutch/images.py` (gate code `image_quality` in `clutch/gates.py`) |
| Layer 2 rubric and schema | `clutch/specs/review_visual.md` |
| Layer 3 candidates, select commit, park and release | `clutch/stages.py` (Check), release: open decision 4 |
| Calibration and the GO verdict | `eval/visual/`, `./dev.py visual-baseline`, `clutch/policy.py` (`visual_baseline` beside the review baseline) |
| How the implementer and reviewers behave | `clutch/specs/implement.md`, `review_visual.md`, `requisition_review.md`, `review.md` |
| The `--kind` list in agent conduct | `CORE_TEMPLATE` in `clutch/hostfiles.py`, rendered by `clutch core` (+9 bytes against the roadmap's byte ledger) |
| Dependencies | `pyproject.toml` extras `images` and `images-embed` |
| Repo-only rules | none needed; `CLAUDE.md` and `AGENTS.md` outside the managed block are unchanged |

## Ticket breakdown

Future tickets. None are authored yet. Each is written with `clutch new`, then `clutch lint` until clean, then `clutch review` until approved, with its tests in new files (`docs/parallel-tickets-plan.md` §7).

| # | Stem | Kind | P | Depends on | Content |
|---|---|---|---|---|---|
| A0 | (agent capture) | evidence | | | The nine facts under "Prerequisite: agent capture", captured as A1's evidence and as the Gemini normalizer's fixture; not a ticket. Fact 7 decides whether `api-provider-client` joins 0.4.0. |
| A1 | `gemini-provider` | feature | P2 | | Part A. Release 0.3.0. |
| B1 | `graphics-kind` | feature | P2 | `closed-sets-single-owner` (roadmap row 19) | Grammar for both modes, template, `--reference` and `--input`, lint, the kind set's one home, `CORE_TEMPLATE` (+9 bytes), authoring guide, requisition spec block. Release 0.4.0. |
| B2 | `graphics-render-check` | feature | P2 | `graphics-kind` | `command` mode: render protocol and artifact checks at Check; implement spec block for both modes. Release 0.4.0. |
| B3 | `route-kinds-filter` | feature | P2 | | `Route.kinds`, kind-aware `resolve()`, judge-independence warning in `doctor` and lint, host-contract inventory. Release 0.4.0. |
| B4 | `image-quality-gate` | feature | P2 | `graphics-kind` | `clutch/images.py`, the `image_quality` gate, the `images` and `images-embed` extras, side-by-side and heatmap artifacts. Release 0.4.0. |
| B5 | `visual-review-surface` | feature | P2 | `graphics-render-check`, `route-kinds-filter`, `image-quality-gate` | `review_visual` spec with rubric, JSON schema, `graphics.judge_samples` majority, per-row verdicts; `review.md` provenance block. Release 0.4.0. |
| B6 | `image-candidates-select` | feature | P2 | `visual-review-surface` | Candidates in Implement, ranking, the select commit, `visual_undecided` park, its release (open decision 4). Release 0.4.0. |
| B7 | `visual-review-baseline` | feature | P2 | `visual-review-surface` | `eval/visual/` fixtures labelled by the AI label panel, `./dev.py visual-baseline`, the `visual_baseline` GO gate at 0.85 agreement; until GO every graphics ticket parks. Release 0.4.0. |

`Runs before`: B2 before `conflict-discard-rerun` (both bump `clutch/specs/implement.md`). B7 before B6 is not required (B6 parks everything until B7 records GO), but B7 should merge in the same release or B6 only ever parks. `contention-authoring-rules` (roadmap row 13) before every ticket here.

Part A and Part B are independent except through A0's fact 7. Within B, each `Depends on` names merged code the ticket uses. A1 is useful to B5 as the judge's routing target and to `evidence-normalize-gemini` as its prerequisite.

## Risks

- **Headless image generation may not exist in the CLI.** A0 fact 7. The fallback is the deferred `api` provider client, scoped to image models; it is a real ticket if the fact comes back negative, and it moves the first image ticket later in 0.4.0.
- **Heavy optional dependencies.** `images-embed` pulls PyTorch. It is a separate extra so that hosts using keypoint presence never install it. Wheel availability on Python 3.14 is A0 fact 9.
- **Judge self-grading.** A judge from the generator's family rates its own work kindly. B3's independence check and B7's calibration are the two guards; the calibration report records which family served the judge.
- **Guessed thresholds.** Every layer-1 default is a guess until B7 measures it; that is why GO gates auto-accept and every ticket parks before GO.
- **Cost.** A `generate` ticket is `candidates` generator calls plus `judge_samples` judge calls per candidate. Both knobs have small maxima (5 and 3) and the defaults (3 and 1) keep a ticket near four model calls.

## Open decisions

Decided 2026-11-16 (`docs/roadmap.md` §6, decision 19): items 2 and 3 take their Proposed option. Item 1 has no Proposed option; a recorded AI design panel settles it before `graphics-kind` is authored.

Decided 2026-11-14 (`docs/roadmap.md` §6, decisions 15-18): scope includes AI-generated images (the point of the provider); the `kinds:` route filter is built now; the visual review decides and only the undecidable parks; grading is the three-layer design above; libraries ship as the two extras. Remaining:

1. **Per-row thresholds as ticket syntax.** B4 lets a ticket tighten a threshold in a mechanical criterion. The exact grammar (`- ssim: >= 0.85 outside region (x, y, w, h)`) is settled by that panel before B1 is authored, with lint pinning it.
2. **Default candidate count and judge samples.** Proposed 3 and 1. Revisit after the first ten graphics tickets with the cost figures from the evidence store.
3. **Where select-commit provenance lives.** Proposed: the select commit message names the candidate index and the judge call's evidence id, so `review.md` can check it. Alternative: a `render.json` lifted beside `checks.json`.

4. **Releasing a `visual_undecided` park.** Previously a person confirmed a selection or rejected it. There is no Proposed option; a recorded AI design panel settles it before `image-candidates-select` is authored.

## Sources

- Gemini CLI headless mode and `stream-json` events: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/headless.md
- Gemini CLI settings, `context.fileName`, `GEMINI_CLI_SYSTEM_SETTINGS_PATH`, precedence: https://geminicli.com/docs/cli/configuration
- System settings for enterprise control: https://geminicli.com/docs/cli/enterprise
- Owner notes on the Gemini image and multimodal models, 2026-11-14 (reproduced under Part A; confirmed by A0).
