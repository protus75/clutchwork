#!/usr/bin/env python3
"""Build and release tasks for this repo.

    ./dev.py                  the full suite (unit under clutch.testguard)
    ./dev.py test [args]      the suite, or named tests (unit under clutch.testguard)
    ./dev.py vscode           package and install the vscode-clutchwork extension
    ./dev.py vscode-package   build a VSIX for Marketplace upload

Every ticket and engine task is a clutch verb, run here as `uv run clutch <verb>`.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(argv: list[str]) -> None:
    print("$", " ".join(argv), flush=True)
    if subprocess.run(argv, cwd=ROOT, check=False).returncode != 0:
        sys.exit(f"dev: `{' '.join(argv)}` failed")


def main() -> None:
    if sys.argv[1:2] == ["test"] and sys.argv[2:]:
        test_args = sys.argv[2:]
        paths = [arg for arg in test_args if arg == "tests" or arg.startswith("tests/")]
        guard = ["-p", "clutch.testguard"] if paths and all(path == "tests/unit" or path.startswith("tests/unit/") for path in paths) else []
        run(["uv", "run", "pytest", "-q", *guard, *test_args])
        return

    if sys.argv[1:] in ([], ["test"]):
        run(["uv", "run", "pytest", "-q", "-p", "clutch.testguard", "tests/unit"])
        run(["uv", "run", "pytest", "-q", "tests/integration"])
        return

    parser = argparse.ArgumentParser(prog="./dev.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="task")
    sub.add_parser("test", help="the suite, or the named tests")
    sub.add_parser("vscode", help="package and install the vscode-clutchwork extension")
    sub.add_parser("vscode-package", help="build a VSIX for Marketplace upload")
    args = parser.parse_args()
    if args.task == "vscode-package":
        with (ROOT / "pyproject.toml").open("rb") as stream:
            version = tomllib.load(stream)["project"]["version"]
        readme = ROOT / "vscode-clutchwork" / "README.md"
        text, count = re.subn(
            r"^Built for \[clutch [^\]]*\]\(https://pypi\.org/project/clutchwork/[^/)]*/\)\.$",
            f"Built for [clutch {version}](https://pypi.org/project/clutchwork/{version}/).",
            readme.read_text(),
            flags=re.MULTILINE,
        )
        if count != 1:
            sys.exit("dev: expected one Built for line in vscode-clutchwork/README.md")
        readme.write_text(text)
        print(f"dev: built for clutch {version}")
        package = json.loads((ROOT / "vscode-clutchwork" / "package.json").read_text())
        output = ROOT / "dist" / f"vscode-clutchwork-{package['version']}.vsix"
        output.parent.mkdir(parents=True, exist_ok=True)
        pack = ["npx", "--yes", "@vscode/vsce", "package", "--no-dependencies", "-o", str(output)]
        print("$", " ".join(pack), flush=True)
        if subprocess.run(pack, cwd=ROOT / "vscode-clutchwork", check=False).returncode != 0:
            sys.exit("dev: packaging vscode-clutchwork failed")
        print(f"dev: upload {output} at https://marketplace.visualstudio.com/manage/publishers/chunkydragon")
        if os.environ.get("WSL_DISTRO_NAME"):
            windows_path = subprocess.run(["wslpath", "-w", str(output)], capture_output=True, text=True, check=False)
            if windows_path.returncode != 0:
                sys.exit("dev: wslpath failed")
            print(f"dev: Windows path {windows_path.stdout.strip()}")
    elif args.task == "vscode":
        # VS Code keeps an extension's old icon and views until its version changes, so every install bumps the patch.
        manifest = ROOT / "vscode-clutchwork" / "package.json"
        package = json.loads(manifest.read_text())
        major, minor, patch = package["version"].split(".")
        package["version"] = f"{major}.{minor}.{int(patch) + 1}"
        manifest.write_text(json.dumps(package, indent="\t") + "\n")
        print(f"dev: vscode-clutchwork version {package['version']}", flush=True)
        with tempfile.TemporaryDirectory() as tmp:
            vsix = str(Path(tmp) / "vscode-clutchwork.vsix")
            pack = ["npx", "--yes", "@vscode/vsce", "package", "--allow-missing-repository", "--skip-license", "--no-dependencies", "-o", vsix]
            print("$", " ".join(pack), flush=True)
            if subprocess.run(pack, cwd=ROOT / "vscode-clutchwork", check=False).returncode != 0:
                sys.exit("dev: packaging vscode-clutchwork failed")
            run(["code", "--install-extension", vsix, "--force"])
        print("dev: run Developer: Reload Window to load it")


if __name__ == "__main__":
    main()
