# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test dev vscode package kept
# relates: [clutch/config.py, dev.py]
# owner: engine
# verified: 148a8874
# hash: e598f3204624b790e1928c961b6a1674c158756495f49813a1db1fb5218d9205
import json
from pathlib import Path
from unittest.mock import Mock

import dev
from clutch import config


def setup_root(tmp_path, monkeypatch):
    ext = tmp_path / "vscode-clutchwork"
    ext.mkdir()
    (ext / "package.json").write_text(json.dumps({"version": "1.2.3"}))
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "9.8.7"\n')
    readme = ext / "README.md"
    readme.write_text("Built for [clutch 0.1.0](https://pypi.org/project/clutchwork/0.1.0/).\n")
    monkeypatch.setattr(dev, "ROOT", tmp_path)
    monkeypatch.setattr(dev.sys, "argv", ["dev.py", "vscode-package"])
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    return readme, tmp_path / "dist" / "vscode-clutchwork-1.2.3.vsix"


def test_existing_package_is_untouched(tmp_path, monkeypatch):
    readme, output = setup_root(tmp_path, monkeypatch)
    original = readme.read_text()
    output.parent.mkdir()
    output.write_bytes(b"existing package")
    run = Mock()
    monkeypatch.setattr(dev.subprocess, "run", run)
    dev.main()
    assert output.read_bytes() == b"existing package"
    assert readme.read_text() == original
    run.assert_not_called()


def test_new_package_restores_readme(tmp_path, monkeypatch):
    readme, output = setup_root(tmp_path, monkeypatch)
    original = readme.read_text()

    def package(argv, *, cwd, check):
        assert "clutch 9.8.7" in readme.read_text()
        output.write_bytes(b"new package")
        return Mock(returncode=0)

    monkeypatch.setattr(dev.subprocess, "run", package)
    dev.main()
    assert output.read_bytes() == b"new package"
    assert readme.read_text() == original


def test_host_declares_package():
    cfg = config.load_config(None, cwd=Path(__file__).resolve().parents[2])
    assert cfg.release.packages[0].argv == ["uv", "run", "python", "dev.py", "vscode-package"]
    assert cfg.release.packages[0].kept == "dist/vscode-clutchwork-*.vsix"
