# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for dev.build_ui_bundle. They check that it inlines the CSS, SVG and esbuild-bundled app.js into clutch/ui/dashboard.html with exact esbuild arguments, and that it writes no output when a source or the esbuild build fails.
# relates: [dev.py]
# owner: dev.py
# verified: f58e6dd7
# hash: 72f624dd18db2ea9481e7a3ed27a952cbc4eceba83de76e8204b19f802d20217
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import dev

ASSETS = {
    "vscode-clutchwork/media/view.css": "shared-css-token",
    "clutch/ui/dashboard.css": "dashboard-css-token",
    "vscode-clutchwork/media/ticket-lifecycle.svg": "<svg>lifecycle-token</svg>",
    "clutch/ui/app.js": "source-token",
}


def sources(root):
    for name, content in ASSETS.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def test_bundle_inlines_assets_and_invokes_esbuild(tmp_path):
    sources(tmp_path)
    runner = Mock(return_value=SimpleNamespace(returncode=0, stdout="bundle-token </script>", stderr=""))
    output = dev.build_ui_bundle(tmp_path, run_cmd=runner)
    assert output == tmp_path / "clutch/ui/dashboard.html"  # Reject a different default destination.
    html = output.read_text()
    for token in ("shared-css-token", "dashboard-css-token", "<svg>lifecycle-token</svg>", r"bundle-token <\/script>"):
        assert token in html  # Reject omission of each distinct source or escaping.
    assert "bundle-token </script>" not in html  # Reject an unescaped script terminator.
    runner.assert_called_once_with(
        [str(tmp_path / "node_modules/.bin/esbuild"), str(tmp_path / "clutch/ui/app.js"), "--bundle", "--format=iife", "--platform=browser", "--global-name=ClutchDashboardApp", "--minify"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )  # Reject omitted or changed bundler arguments.


@pytest.mark.parametrize("missing", ASSETS)
def test_missing_source_refuses_output(tmp_path, missing):
    sources(tmp_path)
    (tmp_path / missing).unlink()
    runner = Mock()
    output = tmp_path / "result.html"
    with pytest.raises(RuntimeError, match="missing source or esbuild"):
        dev.build_ui_bundle(tmp_path, out=output, run_cmd=runner)
    assert not output.exists()  # Reject a partially written bundle.
    runner.assert_not_called()  # Reject invoking esbuild before checking every source.


def test_esbuild_failure_refuses_output(tmp_path):
    sources(tmp_path)
    runner = Mock(return_value=SimpleNamespace(returncode=1, stdout="broken", stderr="build error"))
    output = tmp_path / "result.html"
    with pytest.raises(RuntimeError, match="build error"):
        dev.build_ui_bundle(tmp_path, out=output, run_cmd=runner)
    assert not output.exists()  # Reject output from a failed build.
