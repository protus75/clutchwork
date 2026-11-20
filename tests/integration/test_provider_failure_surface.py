# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test provider failure surface
# relates: [clutch/box.py, clutch/providers.py, clutch/seams.py, tests/integration/test_stages.py]
# owner: engine
# verified: 96e46658
# hash: 7681b839060a53a1cd8d0221a7cdec618b60b71b1f98db6f22d9f357e1b5046e
from clutch.box import BOX_DIR, Box
from clutch.providers import ProviderCallError
from clutch.seams import LocalFileSystem
from tests.integration.test_stages import repo, run  # noqa: F401


def test_implement_provider_failure_uses_implement_surface(repo):
    error = ProviderCallError(
        "codex",
        "quota exhausted",
        rc=1,
        stderr_tail="usage limit reached",
        failure_class="quota_exhausted",
        paved_road="wait for provider 'codex' to recover from quota_exhausted, then retry",
    )
    result, _, config = run(repo, [error])

    assert result.results["implement"].outcome == "infra_error"
    assert [finding.code for finding in result.results["implement"].findings] == ["quota_exhausted"]
    assert "check" not in result.results
    messages = Box(config.state_dir / BOX_DIR, LocalFileSystem()).messages()
    assert len(messages) == 1
    assert (messages[0].message_class, messages[0].stage, messages[0].outcome) == ("failure_report", "implement", "infra_error")
