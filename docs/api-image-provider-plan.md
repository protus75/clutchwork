<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: OpenRouter and fal.ai as kind: api image providers for graphics generate mode: plan
relates: [docs/gemini-graphics-refactor-plan.md]
owner: engine
verified: 1ae5b047
hash: b2405e2705d4317cb766e34136a7ec86eb9abb4f3334492d03bccc48aae6b228
-->
# OpenRouter and fal.ai image providers: plan

Make `mode: generate` graphics tickets work. First re-test whether the current Gemini CLI can write a generated image to disk (G0). Only if it cannot, add clutch's first `kind: api` providers: OpenRouter first, then fal.ai. Each is an HTTP client that sends a prompt and input images to an image model and receives image bytes. The engine makes the call itself in a new `generate` stage. No agent CLI makes it, so the API key never enters an agent's environment. The candidates land where Check already looks for them, so grading (layers 1-3 of `docs/gemini-graphics-refactor-plan.md`) is unchanged.

## Status

Nothing in this plan has been built. Written 2026-11-21 at commit `6717a0b8`. Revised the same day: A0 fact 7 is stale, so G0 now gates everything else. This plan would fill the conditional roadmap row 56 (`api-provider-client`) that `docs/gemini-graphics-refactor-plan.md` (Roadmap, Risks) defers to the first `kind: api` provider.

**Why A0 fact 7 is not enough.** Gemini agent capture A0 fact 7 (`tickets/gemini-provider/evidence/fact-07-image-generation-headless.txt`) found that Gemini CLI calls an image model and then discards the image. That capture ran a global `gemini` 0.49.0 with no extensions on 2026-11-15. The copy clutch runs is the repo's `node_modules/.bin/gemini`, which is 0.70.0 as of 2026-11-21, 21 releases later. Fact 7 never tested Google's image extension for Gemini CLI, which adds a tool that generates an image and saves it to the workspace. So fact 7 does not settle whether the CLI can deliver images today, and G0 re-tests it.

## Why

- **`generate` mode has no proven generator.** `clutch/specs/implement.md` tells the Implement agent to write `candidates:` images to `.clutch/renders/<stem>/a<i>/cand-<k>.<ext>`. Claude, Codex and Qwen have no image model. Gemini CLI is unproven: fact 7 is stale (see Status), and G0 decides.
- **The Gemini credential exists.** `GEMINI_API_KEY` is set on this machine, so `docs/roadmap.md` §6 decision 19's "Gemini has no credential on this machine" is out of date, and G0 can run now.
- **Breadth.** Both services front many image models (Gemini image models, GPT image, FLUX, Seedream, Qwen-Image-Edit) behind one key. That makes it cheap to run the generator on a different model family from the judge (roadmap decision 13).

## Current state

- `Provider.kind` already accepts `api` (`clutch/config.py:79`). `load` refuses it with "kind: api is refused until the api client ships" (`config.py:563-567`), and refuses an api provider on `implement` (`config.py:553-561`, which the comment says stays after the client ships).
- `ADAPTERS` (`clutch/providers.py:832`) maps provider name to a `CliAdapter` subclass. `ProviderLLM` refuses a name with no adapter (`providers.py:935`). `ProviderLLM.kind` is typed `Literal["api", "cli"]` (`providers.py:911`), but only `cli` has any code behind it.
- `Route.kinds` (`config.py:115`) and kind-aware `resolve()` (`providers.py:130-145`) exist, so a `graphics` row can route to a different provider.
- `check_candidates` (`clutch/stages.py:1727`) reads `worktree/.clutch/renders/<stem>/a<i>/cand-<k>.<ext>`, runs `images.judge` (layer 1), the `review_visual` judge (layer 2) and `visual.decide` (layer 3), and commits `clutch(<stem>): select`. It refuses a branch whose diff touches an artifact path or `.clutch/renders`. It does not care who wrote the candidates.
- `review_visual` runs through the driver on a CLI provider, which opens image paths with its read tool. Claude CLI reads images, so a Claude judge already sits in a different family from any Gemini, GPT or FLUX generator. This plan does not touch the judge.
- Engine I/O goes through `clutch/seams.py` (clock, exec, filesystem, notifications). There is no HTTP seam and no HTTP dependency.

## Target design

### 1. Where the call happens: a `generate` stage, not the Implement agent

The rejected alternative is to keep the Implement agent and give it a `clutch image generate` verb to shell out to. That puts the API key in the agent's environment, which breaks the rule "Never pass a provider key to a process that does not need it" (CLAUDE.md §A, "Fenced by gates"). It also leaves the call count, the cost and the capture up to the agent.

The design instead:

- A new surface `generate`, served only by a `kind: api` provider. For a `graphics` ticket whose `## Render` says `mode: generate`, the runner runs the Generate stage instead of Implement. A `generate` ticket's deliverable is the image, and no code changes. `command`-mode and non-graphics tickets keep Implement.
- For each `artifact:` index `i` and each candidate `k` below `candidates:`, Generate makes one call. The call carries the prompt (the ticket's `Goal / Why`, the same text `check_candidates` passes to the judge as `generator_prompt`) and every `input:` image. Generate writes the returned bytes to `.clutch/renders/<stem>/a<i>/cand-<k>.<ext>` in the worktree, uncommitted. Check runs next with no change.
- Every call goes through the driver like any other LLM call, so it gets an evidence record, journal entries, the spend budget, the failure classes and the cooldown.
- The `implement` refusal for api providers in `config.py` stays. `load` gains a matching refusal: `generate` must be served by an api provider whose adapter declares image output.

### 2. Provider and config

No new `Provider` field. Adapters are keyed by provider name, as `ADAPTERS` already is:

```yaml
providers:
  - name: openrouter
    kind: api
    auth: OPENROUTER_API_KEY
    models_by_tier: {low: google/gemini-3.1-flash-image, medium: google/gemini-3.1-flash-image, high: google/gemini-3-pro-image, max: google/gemini-3-pro-image}
    limits: {concurrency: 2}            # usage.cost is reported, so no estimate needed
  - name: fal
    kind: api
    auth: FAL_KEY
    models_by_tier: {low: OPERATOR-SETS-THIS, medium: OPERATOR-SETS-THIS, high: OPERATOR-SETS-THIS, max: OPERATOR-SETS-THIS}
    limits: {concurrency: 2, est_cost_per_call_usd: 0.05}   # fal returns no price
routing:
  - {tier: medium, surface: generate, kinds: [graphics], candidates: [{provider: openrouter}]}
  # review_visual stays on claude (different family from the generator)
```

- `API_ADAPTERS` is a closed dict beside `ADAPTERS`, holding `openrouter` and then `fal`. A `kind: api` provider whose name is not in it is refused with the list, the same way `providers.py:935` refuses an unknown CLI.
- `base_url` stays unset; each adapter owns its endpoint. Setting it is refused, as for the CLIs.
- `auth` names the one env var holding the key. `child_env` is unaffected because no child process is started. The key is read at call time and listed among the configured secrets, so the redaction at the write seam scrubs it from every capture.
- The model names above are examples. The agent capture (C0) records the exact model IDs.

### 3. The HTTP seam and the api client

- **New seam** `http` in `clutch/seams.py`: `request(method, url, headers, body, timeout) -> (status, headers, body)`. The default uses stdlib `urllib.request` run through `asyncio.to_thread`, so there is no new dependency (roadmap decision 12 keeps core light). Tests inject a scripted fake, as for exec.
- **`ApiAdapter`** in `clutch/providers.py`, with the same contract as `CliAdapter`'s outward face: `call(request, served) -> LLMResult`, `reports_cost`, `AUTH_MARKERS`, `LOGIN_ROAD`, and failure classification. The result carries the image bytes and media type for each output. `LLMResult` gains an `images: tuple[bytes, ...]` field (empty for text calls), and one field is the minimum. Generate is the only reader.
- **Failure classes** map onto the existing vocabulary: 401/403 is auth, 402 (OpenRouter out of credits) and 429 are quota, 5xx and timeouts are transient. A 200 response that contains no image (content refusal, text-only reply) is a call error carrying the provider's message, never an empty success.
- **Capture.** The evidence record stores the request with every base64 image replaced by its blob reference, and the response the same way. The `Authorization` header is never recorded.
- **Probe.** `clutch probe <name>` on an api provider makes one minimal authenticated call (OpenRouter: its key or models endpoint; fal: per C0) and reports success or failure with the `LOGIN_ROAD`.

### 4. OpenRouter adapter (first)

- One endpoint, set by C0: either `POST /api/v1/images` (base64 in `data[].b64_json`) or `POST /api/v1/chat/completions` with `modalities: ["image","text"]` (base64 data URL in `choices[0].message.images[].image_url.url`). Input images go as `image_url` content parts holding data URLs. Proposed: `/images` if it accepts input images for edit and fuse, because its reply shape is simpler. Otherwise chat completions.
- `reports_cost = True` from `usage.cost` (USD), so `est_cost_per_call_usd` is not required.
- Why first: it returns the image in the reply with no polling and no download, reports cost, and serves the Gemini image models whose behaviour the owner's 2026-11-14 notes already describe. The same key can later serve an api judge if one is ever needed.

### 5. fal.ai adapter (second)

- Uses the queue API: submit to `https://queue.fal.run/<model-id>` with `Authorization: Key <FAL_KEY>`, poll the returned `status_url` until `COMPLETED`, then fetch `response_url`. Use the returned URLs and never build paths. A failed request also reports `COMPLETED`, so the result body decides the outcome.
- Output images come back as URLs (`images[].url`). The adapter downloads them through the same seam, and the URL host must be one fal serves from, as an allowlist.
- Input images go as data URIs in `image_urls` if C0 shows fal accepts them. Otherwise they are uploaded to fal storage first (C0 decides, and the guide says that inputs leave the machine either way).
- Edit models have different input schemas (`image_urls` vs `image_url`, `num_images`, size fields). The adapter supports one closed set of model IDs whose schema C0 recorded, and refuses any other model with that list. It never guesses a schema.
- `reports_cost = False`, so `limits.est_cost_per_call_usd` is required, as for Gemini CLI.
- Polling waits through the clock seam, and the ticket's existing stuck budget bounds it, so no new timeout knob.

### 6. Docs and help

- `clutch/docs/host-openrouter.md` and `clutch/docs/host-fal.md`, in the shape of `host-gemini.md`: what it is, getting a key, `export`, declaring it, `clutch probe`, routing `generate`, limits and cost, and that input images are sent to a third party. The `docs` verb lists both.
- `clutch/docs/host-contract.md`: `kind: api` stops being refused, the `generate` surface is added, and the shipped-adapter list grows.
- `clutch/docs/host-authoring.md` **Graphics tickets**: `generate` mode needs a `generate` route to an api provider. Without one, lint snags the ticket and names the guide.
- `docs/how-clutch-works.md` §8.1 (providers) and the stage list. `clutch/specs/implement.md` drops its `generate`-mode paragraph, since Implement no longer runs for those tickets (spec minor bump, test pin fenced).
- `clutch/help.py` only if the snapshot gains a vocabulary value (a stage name `generate` in the status view). Then a help entry is added in the same change.

### Where each rule lives

| Rule | Home |
|---|---|
| `kind: api` allowed only on `generate`; `implement` stays cli | `clutch/config.py` (`load`) |
| Adapter set, failure classes, cost, capture | `clutch/providers.py` (`API_ADAPTERS`, `ApiAdapter`) |
| HTTP I/O | `clutch/seams.py` (`http` seam) |
| Which stage runs for `mode: generate` | `clutch/stages.py` / `clutch/runner.py` (Generate stage) |
| How a host sets it up | `clutch/docs/host-openrouter.md`, `host-fal.md`, `host-contract.md` |
| How a generate ticket is written | `clutch/docs/host-authoring.md` (the one authoring source) |
| Agent rules | none; no CLAUDE.md, AGENTS.md or CORE_TEMPLATE change |

## Gate: Gemini CLI re-capture (G0)

G0 runs first, and its result decides whether the rest of this plan is needed. An agent runs the repo's `node_modules/.bin/gemini` (record `--version`, which must equal `pnpm view @google/gemini-cli version`) headless in a scratch workspace with `GEMINI_API_KEY` and an empty `HOME`. It commits stdout, stderr, exit code, the binary path and version, and any image files written, under `tickets/api-provider-client/evidence/g0/`. Establish:

1. **Bare CLI:** whether 0.70.0, given a prompt and two `@path` input images on an image model, writes an image file or emits image bytes on stdout (`stream-json` or `json`). This is fact 7 re-run on the current version.
2. **Image extension:** after installing Google's image extension for Gemini CLI into the scratch `HOME`, whether a headless call with a general model and the write grant calls the extension's tool and saves an image file, where the file lands, and whether the input images reach the image model.
3. **Metering:** whether the `result` event's stats count the image model's tokens when the extension's tool makes the call, or whether that spend is invisible to clutch's meter.
4. **Key handling:** whether the extension reads `GEMINI_API_KEY` from the environment clutch already passes to the gemini child (`child_env`), so no new secret reaches the agent.

**Outcomes:**
- **1 or 2 yields an image file, and 3 meters it:** `generate` mode routes Implement to gemini through `Route.kinds` (`docs/gemini-graphics-refactor-plan.md` B3). C1-C3 are dropped. One ticket installs and pins the extension in the gemini settings files and updates `clutch/docs/host-gemini.md`.
- **An image file, but 3 shows unmetered spend:** the CLI route still works, and that ticket adds a per-call image estimate to gemini's `limits` as well. C1-C3 stay dropped unless that estimate cannot be enforced.
- **No image file either way:** C0-C3 below proceed.

## Prerequisite: agent capture (C0)

C0 runs only if G0 finds no image file. Same shape as Gemini A0. It needs `OPENROUTER_API_KEY` for facts 1-6 and `FAL_KEY` for facts 7-11, and it is skipped per decision 19 until the owner supplies a key. An agent runs plain HTTP calls from a scratch script and commits request, status, headers (key redacted) and body (images saved as files) under `tickets/api-provider-client/evidence/` and `tickets/fal-provider/evidence/`. No adapter or parser in this plan is final until the capture is committed.

OpenRouter:
1. Whether `/api/v1/images` accepts input images (edit and fuse), or only chat completions does. The exact request and reply for each, and the two models picked for `models_by_tier`.
2. The input-image limit per model as observed (2, 4 and 8 inputs), and the output media type and size.
3. Whether `usage.cost` is present on every successful image reply, and its unit.
4. Error bodies and status codes for a bad key, no credits, rate limit, unknown model and a content refusal.
5. Whether a text-only or empty reply can come back with 200.
6. A minimal call for `probe` that costs nothing or close to it.

fal.ai:
7. Queue submit, status and result shapes for two or three edit models (the closed set), including a failed request reporting `COMPLETED`.
8. Whether data URIs are accepted in `image_urls`, or uploading to fal storage is required. The upload call if so.
9. Output URL hosts, and how long the URLs stay valid.
10. Error bodies for a bad key, no balance and a bad input.
11. A minimal call for `probe`.

## Ticket breakdown

Future tickets, none authored yet. Each is written with `clutch ticket new`, then `clutch ticket lint` until clean, then `clutch ticket review` until it approves, with tests in new files (CLAUDE.md §A, hot test files).

| # | Stem | Kind | P | Depends on | Content |
|---|---|---|---|---|---|
| G0 | (agent capture) | evidence | | | Gemini CLI 0.70.0 re-capture, bare and with the image extension. Needs only `GEMINI_API_KEY`, which is set. Decides whether C0-C3 run. |
| C0 | (agent capture) | evidence | | G0 finds no image | Facts 1-11, committed as C1's and C3's evidence. Needs the keys. |
| C1 | `api-provider-client` | feature | P2 | | Roadmap row 56. `http` seam, `ApiAdapter`, `API_ADAPTERS = {openrouter}`, `LLMResult.images`, lifting the api refusal for `generate` only, failure classes, capture with blob refs, `probe` for api, `host-openrouter.md`, host-contract and how-clutch-works updates. |
| C2 | `generate-stage` | feature | P2 | `api-provider-client` | `generate` surface. Runner picks Generate over Implement for `mode: generate`, writes candidates where `check_candidates` reads them, `implement.md` paragraph removed, authoring-guide lint snag for a missing `generate` route. |
| C3 | `fal-provider` | feature | P3 | `api-provider-client` | fal adapter (queue, poll, download, closed model set), `host-fal.md`. Independent of C2. |

`Runs before`: none between C2 and C3. C1 fences `clutch/providers.py` and `clutch/config.py`, so under the parallel overlap rule it serializes with any in-flight ticket fencing either.

What this does not ship: a first real generate ticket and this repo's `config.yaml` routing. Roadmap row 173 (`graphics-generate-first-ticket`) was withdrawn by the owner on 2026-11-21, with no generated-graphics ship clause for 0.4.0. Graphics tickets also still park until a `visual_baseline` GO is recorded (`graphics-select-waits-go`), whatever the generator.

## Risks

- **Inputs leave the machine.** Every `input:` image is sent to a third party, and fal may also host the output on a URL that can be fetched publicly. The guides say so plainly. A host with private assets should not route `generate`.
- **Schema drift on fal.** Each fal model has its own input schema. The closed model set and the refusal of unknown models keep this fail-closed, at the cost of a small change to add a model.
- **Cost.** One ticket costs `candidates × artifacts` image calls. Calls are pre-checked against the ticket budget like any other call. OpenRouter reports the real price. fal relies on the operator's estimate, so its spend can be wrong in either direction.
- **Content refusals.** A refused prompt is a call error with the provider's message, so the ticket fails visibly and is not graded on an empty candidate.
- **Judge independence.** Generator (OpenRouter or fal) and judge (Claude CLI) are different families by construction. The existing `doctor` and lint check still applies if an operator routes `review_visual` to the same family.

## Open decisions

0. **If G0 finds no CLI route, Google's API direct or OpenRouter first.** Calling Google's Gemini API directly (`generateContent` with image output) uses the key and credit already on this machine and involves no third party. OpenRouter reaches more model families with one key. No Proposed option; the owner decides before C1 is authored.
1. **Which service first.** Proposed: OpenRouter (single reply, reported cost, Gemini image models). fal.ai follows as C3.
2. **OpenRouter endpoint.** Proposed: `/api/v1/images` if C0 fact 1 shows it takes input images, otherwise chat completions.
3. **HTTP implementation.** Proposed: stdlib `urllib` behind the seam. The alternative is `httpx` in the `images` extra, which earns its place only if C0 shows a need (streaming, HTTP/2).
4. **Generate replaces Implement for `mode: generate`.** Proposed: yes. A ticket wanting both code and a generated image is split into two tickets.
5. **Release slot.** No Proposed option. The owner places C1-C3 on the roadmap (row 56 is provisional).

## Sources

- OpenRouter image generation: https://openrouter.ai/docs/guides/overview/multimodal/image-generation
- OpenRouter Images API reference: https://openrouter.ai/docs/api/api-reference/images/generate-an-image
- fal.ai queue API: https://fal.ai/docs/model-apis/model-endpoints/queue and https://fal.ai/docs/inference-api/queue/status.md
- Example fal edit model schema: https://fal.ai/models/fal-ai/qwen-image-edit-2511/api
- Gemini A0 fact 7: `tickets/gemini-provider/evidence/fact-07-image-generation-headless.txt`
