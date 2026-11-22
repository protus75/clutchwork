# Review: snag

Sharing preflight across the session works and is covered by tests, but a skipped preflight leaves each new ProviderLLM's adapters with cli_version None, so evidence records for every ticket after the first lose the CLI version.

## Findings

- [logic] clutch/providers.py:272 When `preflight_once` skips the probe it returns `[]` without running `ProviderLLM.preflight`. That method is the only place that sets `adapter.cli_version` (providers.py:962). `prepare_pipeline` and `_preflighted_llm` build a fresh `ProviderLLM`, with fresh adapters, on every dispatch. So every dispatch after the first runs with `cli_version = None`, and that null goes into each call's evidence record (`provider.cli_version`, providers.py:512). `evidence/views.py` groups by it, so per-version stats for every ticket but the first land under `None`. Before this change every dispatch recorded the real version. (do instead: When the probe succeeds, save each provider's `cli_version` on the `ProviderSession` (for example, store it with the key). On a skip, copy those versions onto the new `ProviderLLM`'s adapters, so no `--version` call is needed. Add a case to `tests/unit/test_preflight_once_per_session.py` that checks a second `prepare_pipeline`'s adapters still carry the version.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "d6a4bfdfd324a578c0922e7ca71b2acaffbb774b",
  "stem": "preflight-once-per-session",
  "reviewed_sha": "d6a4bfdfd324a578c0922e7ca71b2acaffbb774b",
  "summary": "Sharing preflight across the session works and is covered by tests, but a skipped preflight leaves each new ProviderLLM's adapters with cli_version None, so evidence records for every ticket after the first lose the CLI version.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/providers.py",
      "line": 272,
      "message": "When `preflight_once` skips the probe it returns `[]` without running `ProviderLLM.preflight`. That method is the only place that sets `adapter.cli_version` (providers.py:962). `prepare_pipeline` and `_preflighted_llm` build a fresh `ProviderLLM`, with fresh adapters, on every dispatch. So every dispatch after the first runs with `cli_version = None`, and that null goes into each call's evidence record (`provider.cli_version`, providers.py:512). `evidence/views.py` groups by it, so per-version stats for every ticket but the first land under `None`. Before this change every dispatch recorded the real version.",
      "paved_road": "When the probe succeeds, save each provider's `cli_version` on the `ProviderSession` (for example, store it with the key). On a skip, copy those versions onto the new `ProviderLLM`'s adapters, so no `--version` call is needed. Add a case to `tests/unit/test_preflight_once_per_session.py` that checks a second `prepare_pipeline`'s adapters still carry the version.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
