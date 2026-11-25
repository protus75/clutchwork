"""The built distributions include the dashboard served by MCP."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the built wheel and sdist both contain the ui-bundle dashboard.html and that the MCP server serves it as the dashboard resource
# relates: [clutch/config.py, clutch/mcp.py, dev.py]
# owner: engine
# verified: 403faee1
# hash: 7072671b1c0f2e3b19c425c1ba29f0de8957e62134297cfd61358256ff133ffd

import subprocess
import tarfile
import zipfile
from pathlib import Path

import dev
from clutch import config
from clutch.mcp import ClutchMCPServer

ROOT = Path(__file__).resolve().parents[2]


def test_dashboard_in_distributions(tmp_path):
    cfg = config.load_config(None, cwd=ROOT)
    assert cfg.release.pre_build == [["uv", "run", "python", "dev.py", "ui-bundle"]]
    bundle = ROOT / "clutch/ui/dashboard.html"
    original = bundle.read_bytes() if bundle.exists() else None
    try:
        dev.build_ui_bundle(root=ROOT)
        subprocess.run(["uv", "build", "--clear", "-o", str(tmp_path / "dist")], cwd=ROOT, check=True, timeout=600)
        (wheel,) = (tmp_path / "dist").glob("*.whl")
        (sdist,) = (tmp_path / "dist").glob("*.tar.gz")
        with zipfile.ZipFile(wheel) as archive:
            data = archive.read("clutch/ui/dashboard.html")
        with tarfile.open(sdist) as archive:
            names = [name for name in archive.getnames() if name.endswith("/clutch/ui/dashboard.html")]
            assert len(names) == 1
            extracted = archive.extractfile(names[0])
            assert extracted is not None and extracted.read() == data
        assert data and data == bundle.read_bytes()
        path = tmp_path / "dashboard.html"
        path.write_bytes(data)
        item = ClutchMCPServer(ui_html_path=path).dispatch("resources/read", {"uri": "ui://clutch/dashboard.html"})["contents"][0]
        assert item["mimeType"] == "text/html;profile=mcp-app"
        assert item["text"].encode() == data
    finally:
        if original is None:
            bundle.unlink(missing_ok=True)
        else:
            bundle.write_bytes(original)
