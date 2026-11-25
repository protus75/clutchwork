# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Regression probe that passes only when clutch_wait_event is visible only to the model and the doctor accepts the portable Antigravity MCP config.
# relates: [clutch/antigravity.py, clutch/mcp.py]
# owner: engine
# verified: 13fb8abf
# hash: 73e4484ad050ce2f1b945c50795899ee41cd71fc6ad665510aee5f57ac839138
import json
import tempfile
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    if not all((root / path).is_file() for path in ("clutch/mcp.py", "clutch/antigravity.py")):
        return "error"
    from clutch import antigravity, mcp

    tools = mcp.ClutchMCPServer().dispatch("tools/list", {})["tools"]
    wait = next(tool for tool in tools if tool["name"] == "clutch_wait_event")
    scratch = root / ".clutch" / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as directory:
        plugin = Path(directory)
        (plugin / "mcp_config.json").write_text(json.dumps(antigravity.portable_mcp_config()))
        valid = antigravity.doctor_finding(plugin, executable_exists=lambda _: True) is None
    return "pass" if wait.get("_meta", {}).get("ui", {}).get("visibility") == ["model"] and valid else "defect"


try:
    result = main()
except Exception:
    result = "error"
print(json.dumps({"regression_result": result}))
raise SystemExit({"pass": 0, "defect": 1, "error": 2}[result])
