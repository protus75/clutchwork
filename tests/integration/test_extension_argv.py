# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test extension argv
# relates: []
# owner: engine
# verified: 148a8874
# hash: 19f6adcf50d1b146158fa0631fb8b64c0d2e1d48e4e37ff9dc871687b2034bcf
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_extension_argv_from_snapshot():
    source = (ROOT / "vscode-clutchwork/extension.js").read_text()
    assert not re.search(r"""devCommand\(\s*['"]""", source)
    assert not re.search(r"""\[\s*['"](review|lint|run|triage|dismiss|serve|stop|order|stats|prompt)['"]""", source)
    assert "--priority" not in source
    assert "--runs-before" not in source
    assert "snap.root" in source
    assert source.count("['view', 'snapshot']") == 1
