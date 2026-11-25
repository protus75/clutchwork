"""Portable Antigravity bundle rendering."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for rendering the portable Antigravity plugin manifest, the MCP config and the bundle file map, including the skills.
# relates: [clutch/antigravity.py]
# owner: clutch/antigravity.py
# verified: 8342251d
# hash: 2e9fd9fb25ea3d75afda4e5a8aa7f3c76ecf9f059f98b5c9befb1501ed2bf730

import json

from clutch import antigravity as ag


def test_manifest():
    manifest = ag.plugin_manifest(version_str="0.7.0")
    assert manifest == {
        "name": "clutchwork",
        "displayName": "ClutchWork",
        "version": "0.7.0",
        "description": "Supervise ClutchWork tickets and engines.",
        "author": "ClutchWork",
        "homepage": "https://github.com/protus75/clutchwork",
        "repository": "https://github.com/protus75/clutchwork",
        "logo": "assets/logo.svg",
        "suggestedPrompts": ["Open the ClutchWork dashboard", "Supervise the Clutch queue (drain-loop)", "Run docs/roadmap.md unattended with serve"],
    }


def test_portable_bundle():
    config = {"mcpServers": {"clutchwork": {"command": "uvx", "args": ["--from", "clutchwork", "clutch", "mcp", "serve"]}}}
    assert ag.portable_mcp_config() == config
    files = ag.portable_bundle_files(version_str="0.7.0", logo_bytes=b"<svg/>")
    assert set(files) == {"plugin.json", "mcp_config.json", "assets/logo.svg", "skills/clutch-drain-loop/SKILL.md", "skills/clutch-plan-drain/SKILL.md", "skills/clutch-plan-serve/SKILL.md"}
    assert files["plugin.json"] == (json.dumps(ag.plugin_manifest("0.7.0"), indent=2) + "\n").encode()
    assert files["mcp_config.json"] == (json.dumps(config, indent=2) + "\n").encode()
    assert files["assets/logo.svg"] == b"<svg/>"
    for name, skill in ag.SKILLS.items():
        assert files[f"skills/{name}/SKILL.md"] == skill.encode()
