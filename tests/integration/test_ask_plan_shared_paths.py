# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks plan-ticket-drain and plan-ticket-serve prompts exempt scheduler.parallel.shared_paths from the fence-overlap authoring wait
# relates: [clutch/ask.py, clutch/config.py, tests/integration/test_config.py]
# owner: engine
# verified: d32c32ad
# hash: c368cefafe7385e1ca3504fa60c645567a8dd3e7b1eada7374ecebbcbe3c0a5f
import pytest

from clutch import ask
from clutch.config import load_config
from tests.integration.test_config import VALID

pytestmark = pytest.mark.disk_io_skip


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
