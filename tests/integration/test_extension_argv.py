import re
from pathlib import Path


def test_extension_argv_from_snapshot():
    source = Path("vscode-clutchwork/extension.js").read_text()
    assert not re.search(r"""devCommand\(\s*['"]""", source)
    assert not re.search(r"""\[\s*['"](review|lint|run|triage|dismiss|serve|stop|order|stats|prompt)['"]""", source)
    assert "--priority" not in source
    assert "--runs-before" not in source
    assert "snap.root" in source
    assert source.count("['view', 'snapshot']") == 1
