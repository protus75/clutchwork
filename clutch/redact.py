"""Redaction seam: one shared filter every captured-stream writer is built with.

Writer-site checklist (extend in the same change that adds a writer of a captured stream):
- attempt-spool writer: clutch/driver.py `Spool`
- engine-log writer: clutch/enginelog.py `EngineLog`
- evidence writer: clutch/evidence/store.py `EvidenceStore.put_blob` (prompt, stdout, stderr and arrival-time blobs from clutch/providers.py `CliAdapter.invoke`)
- harvest writer: clutch/runner.py `harvest` (attempts/<n>/harvest.json)
- retro report writer: clutch/retro.py `Retro.commit_report`
- notification output: clutch/seams.py `CommandNotifications` (stdout and stderr scrubbed before the effect result is journaled)
- journal writer: clutch/journal.py does not scrub; producers scrub captured text before append,
  including clutch/llmeffect.py `llm_call` and clutch/runner.py `harvest_failure` (the harvest_failed signal)
"""

from collections.abc import Mapping

from clutch.config import Config, ConfigSnapshot


def secret_names(config: Config | ConfigSnapshot) -> frozenset[str]:
    return frozenset({p.auth for p in config.providers if p.auth} | {config.release.pypi_token})


class Redactor:
    def __init__(self, secrets: Mapping[str, str]) -> None:
        # An empty value would match everywhere; longest first so an embedded shorter secret cannot split a longer one.
        self._secrets = sorted(((n, v) for n, v in secrets.items() if v), key=lambda nv: -len(nv[1]))

    @classmethod
    def from_config(cls, config: Config | ConfigSnapshot, env: Mapping[str, str]) -> "Redactor":
        """Resolve configured secret names that are set in the environment."""
        return cls({name: env[name] for name in secret_names(config) if name in env})

    def scrub(self, text: str) -> str:
        for name, value in self._secrets:
            text = text.replace(value, f"[REDACTED:{name}]")
        return text
