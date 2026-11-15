"""Carried reproducer for host-inaccessible engine text."""

import json
import os
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    package = root / "clutch"
    hits = []
    count = 0
    try:
        if not package.is_dir():
            raise ValueError("clutch directory is missing")
        for directory, dirs, files in os.walk(package, onerror=lambda error: (_ for _ in ()).throw(error)):
            dirs[:] = [name for name in dirs if name != "__pycache__" and Path(directory, name) != package / "docs"]
            for name in files:
                path = Path(directory, name)
                lines = path.read_text(encoding="utf-8").splitlines()
                count += 1
                hits.extend(f"{path.relative_to(root)}:{number}" for number, line in enumerate(lines, 1) if "dev.py" in line)
        if not count:
            raise ValueError("clutch directory has no scannable files")
    except (OSError, UnicodeError, ValueError) as error:
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
