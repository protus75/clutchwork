"""Packaged plugin assets agree with their production owners."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the packaged Antigravity plugin logo, skill kinds and tool names, and the host documentation match their production owners.
# relates: [clutch/antigravity.py, clutch/ask.py, clutch/mcp.py, tests/fakes.py]
# owner: engine
# verified: 5e56ddef
# hash: 968811d79b47afa06df1ab539c25016ccb4a64e0078f9653a5d7dc98516ca995

import re
from pathlib import Path

from clutch import antigravity, ask, mcp
from tests.fakes import FakeFileSystem

ROOT = Path(__file__).resolve().parents[2]


def test_logo_and_registered_tools():
    assert antigravity.DEFAULT_LOGO_PATH == ROOT / "clutch/assets/logo.png"
    logo = (ROOT / "clutch/assets/logo.png").read_bytes()
    assert logo == (ROOT / "assets/hatchling-512.png").read_bytes()
    assert not (ROOT / "clutch/assets/logo.svg").exists()
    fs = FakeFileSystem()
    fs.write(antigravity.DEFAULT_LOGO_PATH, logo)
    antigravity.install_plugin(plugin_dir=Path("/plugin"), fs=fs, logo_bytes=None, version_str="1")
    assert fs.read_bytes(Path("/plugin/assets/logo.png")) == logo
    for skill in antigravity.SKILLS.values():
        assert set(re.findall(r'kind: "([^"]+)"', skill)) <= set(ask.KINDS)
        assert set(re.findall(r"clutch_[a-z_]+", skill)) <= set(mcp.TOOLS)


def test_documentation():
    for path in ("clutch/docs/host-running.md", "clutch/docs/host-contract.md", "docs/how-clutch-works.md", "README.md"):
        text = (ROOT / path).read_text()
        assert "host antigravity" in text and "--workspace" in text and "host doctor" in text
