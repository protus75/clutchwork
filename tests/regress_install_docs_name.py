"""Carried reproducer for incorrect distribution names in install docs."""

import json
import re
import sys
import tomllib
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    patterns = {
        "README.md": [r"uv add --dev ([A-Za-z0-9._-]+)"],
        "clutch/docs/host-contract.md": [
            r"uv add --dev ([A-Za-z0-9._-]+)",
            r"`([A-Za-z0-9._-]+)==<version>`",
            r"Add dev dependencies `([A-Za-z0-9._-]+)`",
        ],
    }
    hits = []
    try:
        with (root / "pyproject.toml").open("rb") as project_file:
            name = tomllib.load(project_file)["project"]["name"]
        for filename, expressions in patterns.items():
            content = " ".join((root / filename).read_text(encoding="utf-8").split())
            for expression in expressions:
                matches = re.findall(expression, content)
                if not matches:
                    raise ValueError(f"{filename}: no match for {expression}")
                hits.extend(f"{filename}: {match}" for match in matches if match != name)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        print(error, file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    if hits:
        print("\n".join(hits), file=sys.stderr)
        print(json.dumps({"regression_result": "defect"}))
        return 1
    print(json.dumps({"regression_result": "pass"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
