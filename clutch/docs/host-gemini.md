# Gemini provider setup

## What it is

Google's Gemini CLI (`gemini`) is a clutch provider for text work. clutch passes the prompt, tool grant, conduct file, and workspace trust itself, so no gemini configuration file is needed. Image generation does not work through it: the CLI discards generated images.

## Install

Run `clutch provider install gemini` to install a pnpm dev dependency in the host, or `pnpm add -g @google/gemini-cli@latest` for a global install.

## Authenticate

Create an API key in Google AI Studio, export `GEMINI_API_KEY` in the environment that starts clutch, and declare `auth: GEMINI_API_KEY` in the provider. `clutch config init` writes that line when it finds gemini. The CLI reads exactly that variable. Declaring it makes clutch pass the key only to gemini calls and redact it from captures. Google OAuth login and Vertex AI are not covered.

## Pick models

The CLI has no listing command, so `clutch config update` lists no gemini models and prints a problem line. The hand test called `gemini-3.1-pro-preview` and `gemini-3.1-flash-lite`, and the API lists `gemini-3-flash-preview`. A name ending in `flash` is rewritten by the CLI: `gemini-2.5-flash` was served as `gemini-3.6-flash`. clutch records the served name as the call's model. `gemini-2.5-pro` is listed but returns 404 for new keys. Confirm every choice with `clutch provider probe gemini`.

## Declare it in config.yaml

```yaml
name: gemini
kind: cli
package: "@google/gemini-cli"
auth: GEMINI_API_KEY
models_by_tier: {low: gemini-3.1-flash-lite, medium: gemini-3-flash-preview, high: gemini-3.1-pro-preview, max: gemini-3.1-pro-preview}
limits: {concurrency: 1, est_cost_per_call_usd: 0.25}
```

## Probe it

Run `clutch provider probe gemini`; it prints `gemini <model>: ok`. `Please set an Auth method` means the key is not exported in clutch's environment; `API key not valid` means the key is wrong; a model error means the id is not served.

## Route it

For example:

```yaml
{tier: medium, surface: review, candidates: [{provider: claude}, {provider: gemini}]}
```

Preflight probes every routed model at drain start.

## Conduct file

gemini reads `AGENTS.md`, where `clutch core` writes the managed block once gemini is routed. It also loads any `GEMINI.md` in the working directory or home, which clutch cannot switch off; keep host rules in `AGENTS.md`.

## Limits

The CLI reports tokens, never USD, so `est_cost_per_call_usd` is the per-call charge; edit it to your prices. Each call carries about 8k input tokens of the CLI's own system prompt. A daily-quota error cools gemini for `limits.quota_window_minutes`. A prompt over 8 MiB is truncated without an error. Each call leaves a full transcript under `~/.gemini/tmp/`, and an API error writes `/tmp/gemini-client-error-*.json` holding the prompt context. A refusal is a successful reply.
