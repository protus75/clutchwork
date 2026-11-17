from pathlib import Path
from unittest.mock import Mock

import pytest

import dev


def test_test_passes_leading_options_to_pytest(monkeypatch):
    monkeypatch.setattr(dev.sys, "argv", ["dev.py", "test", "--durations=25", "-k", "foo"])
    run = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr(dev.subprocess, "run", run)
    dev.main()
    run.assert_called_once_with(
        ["uv", "run", "pytest", "-q", "--durations=25", "-k", "foo"],
        cwd=dev.ROOT,
        check=False,
    )  # Leading options must reach pytest in their original order.

    run.reset_mock()
    monkeypatch.setattr(dev.sys, "argv", ["dev.py", "vscode-package", "--bogus"])
    with pytest.raises(SystemExit) as error:
        dev.main()
    assert error.value.code == 2  # A surviving command must reject unknown options.
    run.assert_not_called()


@pytest.fixture
def vscode_package(tmp_path, monkeypatch):
    extension = tmp_path / "vscode-clutchwork"
    extension.mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "9.8.7"\n')
    (extension / "README.md").write_text("# clutch tickets\n\nBuilt for [clutch 0.0.1](https://pypi.org/project/clutchwork/0.0.1/).\n\ntail\n")
    (extension / "package.json").write_text('{"version": "1.2.3"}')
    monkeypatch.setattr(dev, "ROOT", tmp_path)
    monkeypatch.setattr(dev.sys, "argv", ["dev.py", "vscode-package"])
    return tmp_path / "dist" / "vscode-clutchwork-1.2.3.vsix"


def test_vscode_package_prints_windows_path_under_wsl(vscode_package, monkeypatch, capsys):
    monkeypatch.setenv("WSL_DISTRO_NAME", "DifferentDistro")
    windows_path = r"\\wsl.localhost\Distro\repo\dist\vscode-clutchwork-1.2.3.vsix"
    run = Mock(side_effect=[Mock(returncode=0), Mock(returncode=0, stdout=f" {windows_path}\n")])
    monkeypatch.setattr(dev.subprocess, "run", run)

    dev.main()

    assert run.call_args_list[1] == ((["wslpath", "-w", str(vscode_package)],), {"capture_output": True, "text": True, "check": False})  # Translate the packaged VSIX, not another path.
    output = capsys.readouterr().out.splitlines()
    assert f"dev: upload {vscode_package} at https://marketplace.visualstudio.com/manage/publishers/chunkydragon" in output  # Keep the existing upload instruction.
    assert f"dev: Windows path {windows_path}" in output  # Print stripped wslpath output, not a path built from the distro.


def test_vscode_package_skips_wslpath_outside_wsl(vscode_package, monkeypatch, capsys):
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    run = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr(dev.subprocess, "run", run)

    dev.main()

    run.assert_called_once_with(
        ["npx", "--yes", "@vscode/vsce", "package", "--no-dependencies", "-o", str(vscode_package)], cwd=dev.ROOT / "vscode-clutchwork", check=False
    )  # No translation subprocess outside WSL.
    assert "Windows path" not in capsys.readouterr().out  # Do not print a fabricated path outside WSL.


def test_vscode_package_stops_when_wslpath_fails(vscode_package, monkeypatch, capsys):
    monkeypatch.setenv("WSL_DISTRO_NAME", "Distro")
    run = Mock(side_effect=[Mock(returncode=0), Mock(returncode=1, stdout="failed output")])
    monkeypatch.setattr(dev.subprocess, "run", run)

    with pytest.raises(SystemExit) as error:
        dev.main()

    assert "wslpath" in str(error.value.code)  # Identify the failing translation command.
    assert "Windows path" not in capsys.readouterr().out  # Never print failed output as a path.
    assert run.call_args.args[0] == ["wslpath", "-w", str(vscode_package)]  # The failure must come from translating the packaged VSIX.


def test_vscode_package_stamps_clutch_version(vscode_package, monkeypatch, capsys):
    monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    readme = dev.ROOT / "vscode-clutchwork" / "README.md"
    original = readme.read_text()
    packaged = []

    def fake_run(argv, *, cwd, check):
        if argv[0] == "npx":
            packaged.append(readme.read_text())
        return Mock(returncode=0)

    monkeypatch.setattr(dev.subprocess, "run", fake_run)
    dev.main()
    expected = "# clutch tickets\n\nBuilt for [clutch 9.8.7](https://pypi.org/project/clutchwork/9.8.7/).\n\ntail\n"
    assert packaged == [expected]  # The package must see the engine version and intact surrounding text.
    assert readme.read_text() == original  # Restore the tracked README after packaging.
    assert "dev: built for clutch 9.8.7" in capsys.readouterr().out  # Report the engine version, not the extension version.


def test_vscode_package_stops_without_built_for_line(vscode_package, monkeypatch):
    readme = dev.ROOT / "vscode-clutchwork" / "README.md"
    original = "# clutch tickets\n\ntail\n"
    readme.write_text(original)
    run = Mock()
    monkeypatch.setattr(dev.subprocess, "run", run)
    with pytest.raises(SystemExit) as error:
        dev.main()
    assert str(error.value.code).startswith("dev:") and "Built for" in str(error.value.code)  # Explain the missing marker.
    run.assert_not_called()  # Do not package without a version marker.
    assert readme.read_text() == original  # Do not silently append a marker.


@pytest.mark.parametrize("verb", ["status", "lint", "new", "confirm", "drain", "suggest"])
def test_engine_verbs_are_not_dev_subcommands(monkeypatch, verb):
    monkeypatch.setattr(dev.sys, "argv", ["dev.py", verb])
    run = Mock()
    monkeypatch.setattr(dev.subprocess, "run", run)
    with pytest.raises(SystemExit) as error:
        dev.main()
    assert error.value.code == 2  # Each engine verb must be rejected by the parser.
    run.assert_not_called()  # Rejection must not launch a subprocess.
