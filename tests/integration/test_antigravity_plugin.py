"""Packaged plugin assets agree with their production owners."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the packaged Antigravity plugin logo, skill kinds and tool names, and the host documentation match their production owners.
# relates: [clutch/antigravity.py, clutch/ask.py, clutch/mcp.py, tests/fakes.py]
# owner: engine
# verified: 1324cf62
# hash: c57d3d9e3a499bd165d34577f7593f7e9dd447f77e09b56bd48904c03b830c77

import re
from pathlib import Path

from clutch import antigravity, ask, mcp
from tests.fakes import FakeFileSystem

ROOT = Path(__file__).resolve().parents[2]


def test_logo_and_registered_tools():
    logo = (ROOT / "clutch/assets/logo.svg").read_bytes()
    assert logo.startswith(b"<svg") and logo == (ROOT / "vscode-clutchwork/media/icon.svg").read_bytes()
    fs = FakeFileSystem()
    fs.write(antigravity.DEFAULT_LOGO_PATH, logo)
    antigravity.install_plugin(plugin_dir=Path("/plugin"), fs=fs, version_str="1")
    assert fs.read_bytes(Path("/plugin/assets/logo.svg")) == logo
    for skill in antigravity.SKILLS.values():
        assert set(re.findall(r'kind: "([^"]+)"', skill)) <= set(ask.KINDS)
        assert set(re.findall(r"clutch_[a-z_]+", skill)) <= set(mcp.TOOLS)


def test_documentation():
    for path in ("clutch/docs/host-running.md", "clutch/docs/host-contract.md", "docs/how-clutch-works.md", "README.md"):
        text = (ROOT / path).read_text()
        assert "host antigravity" in text and "--workspace" in text and "host doctor" in text
