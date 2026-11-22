# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Check that a provider failure during Implement is reported as an implement infra_error with a matching box failure report
# relates: [clutch/box.py, clutch/providers.py, clutch/seams.py, tests/integration/test_stages.py]
# owner: clutch/stages.py
# verified: d32c32ad
# hash: 016c4369abf8b6ef750094330ce427f2a7b1eb968833ab9baac401a1ec0a9dee
import pytest

from clutch.box import BOX_DIR, Box
from clutch.providers import ProviderCallError
from clutch.seams import LocalFileSystem
from tests.integration.test_stages import repo, run  # noqa: F401

pytestmark = pytest.mark.disk_io_skip


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
