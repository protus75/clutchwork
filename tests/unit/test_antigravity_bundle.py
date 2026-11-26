"""Portable Antigravity bundle rendering."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for rendering the portable Antigravity plugin manifest, the MCP config and the bundle file map, including the skills.
# relates: [clutch/antigravity.py]
# owner: clutch/antigravity.py
# verified: c07897c9
# hash: 0685c12cd421909f994d7e489d865edbdf8bbce8d465b89e87662c9cb0b7baaf

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
        "logo": "assets/logo.png",
        "suggestedPrompts": ["Open the ClutchWork dashboard", "Supervise the Clutch queue (drain-loop)", "Run docs/roadmap.md unattended with serve"],
    }


def test_portable_bundle():
    config = {"mcpServers": {"clutchwork": {"command": "uvx", "args": ["--from", "clutchwork", "clutch", "mcp", "serve"]}}}
    assert ag.portable_mcp_config() == config
    files = ag.portable_bundle_files(version_str="0.7.0", logo_bytes=b"<svg/>")
    assert set(files) == {
        "plugin.json",
        "mcp_config.json",
        "hooks.json",
        "assets/logo.png",
        "skills/clutch-drain-loop/SKILL.md",
        "skills/clutch-plan-drain/SKILL.md",
        "skills/clutch-plan-serve/SKILL.md",
    }
    assert files["plugin.json"] == (json.dumps(ag.plugin_manifest("0.7.0"), indent=2) + "\n").encode()
    assert files["mcp_config.json"] == (json.dumps(config, indent=2) + "\n").encode()
    assert files["assets/logo.png"] == b"<svg/>"
    for name, skill in ag.SKILLS.items():
        assert files[f"skills/{name}/SKILL.md"] == skill.encode()
