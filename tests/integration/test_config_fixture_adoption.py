"""Keep the serve config chain on its shared builder and edit helper."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Guards that the serve config test chain uses the shared build_config and amend_config helpers instead of inline YAML provider literals or local dumps.
# relates: [tests/config_fixture.py, tests/integration/test_cli.py, tests/integration/test_stages.py, tests/integration/test_providers.py]
# owner: engine
# verified: 6f94fa01
# hash: 2b9ad036ff93fc42ab0f98e5a7a20427fde29edd1d4a0274929268a039caf326

import ast
import re
from pathlib import Path

import pytest

BUILDERS = (
    "tests/integration/test_cli.py",
    "tests/integration/test_stages.py",
    "tests/integration/test_providers.py",
    "tests/harness/shakeout/bench.py",
)
EDITORS = ("tests/integration/serve_rig.py", "tests/integration/test_serve_parallel_admission.py")
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("path", BUILDERS + EDITORS)
def test_shared_config_adoption(path):
    source = (ROOT / path).read_text()
    # Reintroducing a YAML config literal duplicates the provider defaults again.
    assert re.search(r"^\s*providers:", source, re.MULTILINE) is None
    helper = "build_config" if path in BUILDERS else "amend_config"
    # A local helper or an unrelated import does not adopt the canonical owner.
    assert any(isinstance(node, ast.ImportFrom) and node.module == "tests.config_fixture" and any(alias.name == helper for alias in node.names) for node in ast.walk(ast.parse(source)))
    if path in EDITORS:
        # An editor retaining its own dump bypasses the shared top-level edit behavior.
        assert "yaml.safe_dump" not in source
