# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the rendered plan-ticket-drain and plan-ticket-serve prompts let a row skip the fence-overlap wait for paths listed in scheduler.parallel.shared_paths.
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: bce07f02
# hash: 4ec90563c0d4e057659373c5ceb1929cca560bb42408d37c3176dde8f113c4b5
import pytest

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID


@pytest.mark.parametrize("kind", ["plan-ticket-drain", "plan-ticket-serve"])
def test_authoring_overlap_exempts_shared_paths(kind, tmp_path):
    (tmp_path / "config.yaml").write_text(VALID)
    config = load_config(None, cwd=tmp_path)
    prompt = ask.render(kind, "", config, tmp_path)

    assert (
        "Author a row only when no confirmed, unmerged ticket fences a file the row will change, "
        "except paths listed in `scheduler.parallel.shared_paths` in config.yaml; "
        "otherwise wait for that ticket to merge."
    ) in prompt
