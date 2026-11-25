"""Exercise shared renderers and their VS Code adapters in Node."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Runs the shared UI renderer and VS Code webview draw-failure Node harnesses and checks view.css theme-variable fallbacks.
# relates: [tests/ui_shared_renderers.js, tests/vscode_draw_failure.js, vscode-clutchwork/media/view.css]
# owner: engine
# verified: 4fded5bb
# hash: ff4e143821c57d61cc9848797a1533816c2909b27bdd2ca0293f26b4abd3061c

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def run(*args):
    return subprocess.run(["node", *map(str, args)], capture_output=True, text=True, check=True, timeout=10).stdout


def test_shared_renderers():
    run(ROOT / "tests/ui_shared_renderers.js")


@pytest.mark.parametrize("view,scenario", [(v, s) for v in ("view", "box", "detail") for s in ("valid", "invalid")] + [(v, "error") for v in ("view", "box")])
def test_webview_errors(view, scenario):
    result = json.loads(run(ROOT / "tests/vscode_draw_failure.js", view, scenario))
    if scenario == "valid":
        assert "cannot draw" not in result["text"]
    else:
        assert result["text"].startswith("snapshot failed: boom" if scenario == "error" else "cannot draw the clutch snapshot:")
        assert result["message"] == {"type": "readme"}


def test_css_fallbacks():
    css = (ROOT / "vscode-clutchwork/media/view.css").read_text()
    for value in (
        "--clutch-merged: var(--vscode-clutchwork-merged, var(--vscode-scmGraph-historyItemRemoteRefColor, #B180D7))",
        "--clutch-queued: var(--vscode-clutchwork-queued, var(--vscode-scmGraph-historyItemRefColor, #3794FF))",
        "--clutch-blocked: var(--vscode-clutchwork-blocked, var(--vscode-scmGraph-historyItemBaseRefColor, #EA5C00))",
        "var(--vscode-font-family, var(--font-sans, system-ui, -apple-system, sans-serif))",
        "var(--vscode-font-size, var(--font-text-sm-size, 13px))",
        "var(--vscode-foreground, var(--color-text-primary, inherit))",
        "var(--vscode-descriptionForeground, var(--color-text-secondary, #71717a))",
        "var(--vscode-list-hoverBackground, var(--color-background-secondary, rgba(128, 128, 128, 0.12)))",
        "var(--vscode-sideBar-background, var(--vscode-editor-background, var(--color-background-primary, transparent)))",
        "var(--vscode-list-inactiveSelectionBackground, var(--color-background-tertiary, rgba(128, 128, 128, 0.2)))",
        "var(--vscode-editorHoverWidget-border, var(--color-border-primary, rgba(128, 128, 128, 0.3)))",
        "var(--vscode-textLink-foreground, var(--color-text-accent, #3794ff))",
        "var(--vscode-editor-background, var(--color-background-primary, #1e1e1e))",
    ):
        assert css.count(value) == (5 if "var(--vscode-descriptionForeground," in value else 1)
