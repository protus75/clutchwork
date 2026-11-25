"""Install the Antigravity plugin and inspect its MCP configuration."""

import json
import os
import shutil
import sys
from collections.abc import Callable, Mapping
from importlib.metadata import version
from pathlib import Path

from clutch.seams import FileSystem, LocalFileSystem

PLUGIN_NAME = "clutchwork"
DISPLAY_NAME = "ClutchWork"
MCP_SERVER_NAME = "clutchwork"
MCP_ARGS = ("-m", "clutch", "mcp", "serve")
DEFAULT_LOGO_PATH = Path(__file__).parent / "assets" / "logo.svg"
SUGGESTED_PROMPTS = ["Open the ClutchWork dashboard", "Supervise the Clutch queue (drain-loop)", "Run docs/roadmap.md unattended with serve"]


def _skill(name, description, kind, tools):
    return f'''---
name: {name}
description: {description}
---

Call `clutch_prompt` with kind: "{kind}" to obtain the canonical spec and follow it.
Bind the spec's tools to {tools}.
'''


SKILLS = {
    "clutch-drain-loop": _skill("clutch-drain-loop", "Supervise the Clutch queue.", "drain-loop", "`clutch_wait_event` and `clutch_open_dashboard`"),
    "clutch-plan-drain": _skill("clutch-plan-drain", "Plan tickets and supervise a drain.", "plan-ticket-drain", "`invoke_subagent`, `clutch_wait_event`, and `clutch_open_dashboard`"),
    "clutch-plan-serve": _skill("clutch-plan-serve", "Plan tickets and supervise serve.", "plan-ticket-serve", "`invoke_subagent`, `clutch_wait_event`, and `clutch_open_dashboard`"),
}


def default_plugin_dir(env: Mapping[str, str] | None = None) -> Path | None:
    home = ((os.environ if env is None else env).get("HOME") or "").strip()
    return Path(home) / ".gemini" / "config" / "plugins" / PLUGIN_NAME if home else None


def plugin_manifest(version_str: str | None = None) -> dict[str, object]:
    return {
        "name": PLUGIN_NAME,
        "displayName": DISPLAY_NAME,
        "description": "Supervise ClutchWork tickets and engines.",
        "version": version_str if version_str is not None else version("clutchwork"),
        "logo": "assets/logo.svg",
        "suggestedPrompts": SUGGESTED_PROMPTS,
    }


def mcp_config(executable: str | Path | None = None) -> dict[str, object]:
    return {"mcpServers": {MCP_SERVER_NAME: {"command": str(executable or sys.executable), "args": list(MCP_ARGS)}}}


def install_plugin(
    *, plugin_dir: Path, fs: FileSystem, executable: str | Path | None = None, logo_bytes: bytes | None = None, logo_path: Path = DEFAULT_LOGO_PATH, version_str: str | None = None
) -> list[Path]:
    files = {
        plugin_dir / "plugin.json": (json.dumps(plugin_manifest(version_str), indent=2) + "\n").encode(),
        plugin_dir / "mcp_config.json": (json.dumps(mcp_config(executable), indent=2) + "\n").encode(),
        plugin_dir / "assets/logo.svg": fs.read_bytes(logo_path) if logo_bytes is None else logo_bytes,
        **{plugin_dir / "skills" / name / "SKILL.md": text.encode() for name, text in SKILLS.items()},
    }
    for path, data in files.items():
        fs.write(path, data)
    return sorted(files)


def install_workspace_skills(*, repo: Path, fs: FileSystem) -> list[Path]:
    files = {repo / ".agents/skills" / name / "SKILL.md": text.encode() for name, text in SKILLS.items()}
    for path, data in files.items():
        fs.write(path, data)
    return sorted(files)


def _executable_exists(command: str) -> bool:
    if os.sep in command or (os.altsep and os.altsep in command):
        return Path(command).is_file() and os.access(command, os.X_OK)
    return shutil.which(command) is not None


def doctor_finding(plugin_dir: Path | None, *, fs: FileSystem | None = None, dir_exists: Callable[[Path], bool] | None = None, executable_exists: Callable[[str], bool] | None = None) -> str | None:
    if plugin_dir is None or not (dir_exists or Path.is_dir)(plugin_dir):
        return None
    fs = fs or LocalFileSystem()
    try:
        config = json.loads(fs.read_bytes(plugin_dir / "mcp_config.json"))
        server = config["mcpServers"][MCP_SERVER_NAME]
        command = server["command"]
        if isinstance(command, str) and command.strip() and server["args"] == list(MCP_ARGS) and (executable_exists or _executable_exists)(command):
            return None
    except OSError, ValueError, UnicodeDecodeError, KeyError, TypeError:
        pass
    return "Antigravity MCP configuration is missing or drifted; run `clutch host antigravity`"
