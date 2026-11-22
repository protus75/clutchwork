# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the drafts prompt lists stems in order with ticket paths, configured state dir, confirm/reject verdicts and appended host notes
# relates: [clutch/ask.py, clutch/config.py, clutch/specs/__init__.py, tests/integration/test_config.py]
# owner: engine
# verified: d32c32ad
# hash: a1cd71ecfcff7d765731047236aceaf388ed49840aded0a93e2a49414da63854
import pytest

from clutch import ask, specs
from clutch.config import load_config
from tests.integration.test_config import VALID

pytestmark = pytest.mark.disk_io_skip


def test_render_drafts(tmp_path):
    (tmp_path / "config.yaml").write_text(VALID.replace("state_dir: .clutch", "state_dir: custom/state"))
    config = load_config(None, cwd=tmp_path)
    config.ask_notes = "specific guidance"
    text = ask.render("drafts", ["a-one", "b-two"], config, tmp_path)
    assert text.index("- a-one: tickets/a-one/ticket.md") < text.index("- b-two: tickets/b-two/ticket.md")  # Neither a fixed path nor reversed stems works.
    assert "custom/state/box/" in text  # The default state path is wrong.
    for expected in ('"Recommendation"', "clutch ticket confirm --yes", "clutch ticket reject --yes", "gold plating"):
        assert expected in text  # Omitting either verdict or its bar loses instructions.
    assert text.endswith(f"{specs.data_open('host_notes')}\nspecific guidance\n{specs.data_close('host_notes')}\n")  # Notes must be appended as data.
