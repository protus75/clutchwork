<!-- clutch:meta
schema: clutch.meta/1.0
kind: guide
purpose: Host guide for installing and signing in to the Antigravity CLI (agy), declaring it in config.yaml, probing it and adding it to routing.
relates: [clutch/providers.py, clutch/config.py, clutch/evidence/antigravity.py]
owner: engine
verified: 69d790e1
hash: 1e8f1645f67947360589c78b4583961cc510de798deb9bd299c5abaad67df9ea
-->
# Antigravity provider setup

Antigravity CLI (`agy`) is a CLI provider using ambient login. Install it with the installer at https://antigravity.google/cli/install.sh; it installs `agy` to `~/.local/bin/agy`. Ensure that directory is on `PATH`, then run `agy` interactively to sign in.

Run `clutch config update` to list available models. Declare the provider in `config.yaml` without a pnpm package:

```yaml
name: antigravity
kind: cli
models_by_tier: {low: gemini-3.8-flash-low, medium: gemini-4-neon-medium, high: gemini-4-neon-high, max: gemini-4-carbon-high}
limits: {concurrency: 1, est_cost_per_call_usd: 0.25}
```

Run `clutch provider probe antigravity` to check the login and models, then add `antigravity` as a routing candidate. `clutch host core` manages the `AGENTS.md` conduct file used by this provider. The stream reports token usage but no cost, so set `est_cost_per_call_usd` to the desired flat estimate and configure concurrency and token limits for your account.
