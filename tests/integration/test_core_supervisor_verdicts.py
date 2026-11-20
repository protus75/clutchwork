# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test core supervisor verdicts
# relates: [clutch/hostfiles.py]
# owner: clutch/hostfiles.py
# verified: 148a8874
# hash: 0bd5303d67d8354295609aad88b3d0a4f255058eaf3ab305b9bf80fe127ab414
from pathlib import Path

import pytest

from clutch.hostfiles import BEGIN, CORE_TEMPLATE, END


@pytest.mark.parametrize("name", ["CLAUDE.md", "AGENTS.md", "hosts/fixture/CLAUDE.md"])
def test_managed_block_matches_template(name):
    data = (Path(__file__).resolve().parents[2] / name).read_bytes()
    assert data.split(BEGIN, 1)[1].split(END, 1)[0] == b"\n" + CORE_TEMPLATE
