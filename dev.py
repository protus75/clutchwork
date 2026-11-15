#!/usr/bin/env python3
"""Build and release tasks for this repo.

    ./dev.py                  the full suite
    ./dev.py test [args]      the suite, or the named tests (args go to pytest)
    ./dev.py publish          bump the patch version, build and upload the release
    ./dev.py vscode           package and install the vscode-chupa extension
    ./dev.py vscode-package   build a VSIX for Marketplace upload

Every ticket and engine task is a chupa verb, run here as `uv run chupa <verb>`.
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
    if sys.argv[1:2] == ["test"]:
        run(["uv", "run", "pytest", "-q", *sys.argv[2:]])
        return

    parser = argparse.ArgumentParser(prog="./dev.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="task")
    sub.add_parser("test", help="the suite, or the named tests")
    sub.add_parser("publish", help="bump the patch version, build and upload the release")
    sub.add_parser("vscode", help="package and install the vscode-chupa extension")
    sub.add_parser("vscode-package", help="build a VSIX for Marketplace upload")
    args = parser.parse_args()
    if args.task is None:
        run(["uv", "run", "pytest", "-q"])
    elif args.task == "publish":
        if not os.environ.get("UV_PUBLISH_TOKEN"):
            sys.exit("dev: set UV_PUBLISH_TOKEN to publish")
        run(["uv", "version", "--bump", "patch"])
        with tempfile.TemporaryDirectory() as tmp:
            run(["uv", "build", "-o", tmp])
            run(["uv", "publish", *(str(path) for path in sorted(Path(tmp).iterdir()))])
    elif args.task == "vscode-package":
        with (ROOT / "pyproject.toml").open("rb") as stream:
            version = tomllib.load(stream)["project"]["version"]
        readme = ROOT / "vscode-chupa" / "README.md"
        text, count = re.subn(
            r"^Built for \[chupa [^\]]*\]\(https://pypi\.org/project/chupa/[^/)]*/\)\.$",
            f"Built for [chupa {version}](https://pypi.org/project/chupa/{version}/).",
            readme.read_text(),
            flags=re.MULTILINE,
        )
        if count != 1:
            sys.exit("dev: expected one Built for line in vscode-chupa/README.md")
        readme.write_text(text)
        print(f"dev: built for chupa {version}")
        package = json.loads((ROOT / "vscode-chupa" / "package.json").read_text())
        output = ROOT / "dist" / f"vscode-chupa-{package['version']}.vsix"
        output.parent.mkdir(parents=True, exist_ok=True)
        pack = ["npx", "--yes", "@vscode/vsce", "package", "--no-dependencies", "-o", str(output)]
        print("$", " ".join(pack), flush=True)
        if subprocess.run(pack, cwd=ROOT / "vscode-chupa", check=False).returncode != 0:
            sys.exit("dev: packaging vscode-chupa failed")
        print(f"dev: upload {output} at https://marketplace.visualstudio.com/manage/publishers/chunkydragon")
        if os.environ.get("WSL_DISTRO_NAME"):
            windows_path = subprocess.run(["wslpath", "-w", str(output)], capture_output=True, text=True, check=False)
            if windows_path.returncode != 0:
                sys.exit("dev: wslpath failed")
            print(f"dev: Windows path {windows_path.stdout.strip()}")
    elif args.task == "vscode":
        # VS Code keeps an extension's old icon and views until its version changes, so every install bumps the patch.
        manifest = ROOT / "vscode-chupa" / "package.json"
        package = json.loads(manifest.read_text())
        major, minor, patch = package["version"].split(".")
        package["version"] = f"{major}.{minor}.{int(patch) + 1}"
        manifest.write_text(json.dumps(package, indent="\t") + "\n")
        print(f"dev: vscode-chupa version {package['version']}", flush=True)
        with tempfile.TemporaryDirectory() as tmp:
            vsix = str(Path(tmp) / "vscode-chupa.vsix")
            pack = ["npx", "--yes", "@vscode/vsce", "package", "--allow-missing-repository", "--skip-license", "--no-dependencies", "-o", vsix]
            print("$", " ".join(pack), flush=True)
            if subprocess.run(pack, cwd=ROOT / "vscode-chupa", check=False).returncode != 0:
                sys.exit("dev: packaging vscode-chupa failed")
            run(["code", "--install-extension", vsix, "--force"])
        print("dev: run Developer: Reload Window to load it")


if __name__ == "__main__":
    main()
