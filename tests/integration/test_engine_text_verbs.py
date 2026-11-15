"""Engine text must name host-accessible operator verbs."""

import os
from pathlib import Path


def test_no_engine_text_names_dev_py():
    root = Path(__file__).resolve().parents[2]
    hits = []
    visited = set()
    for directory, dirs, files in os.walk(root / "chupa"):
        visited.add(Path(directory))
        dirs[:] = [name for name in dirs if name != "__pycache__"]
        for name in files:
            path = Path(directory, name)
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError as error:
                raise AssertionError(f"{path.relative_to(root)} is not UTF-8; prune it deliberately") from error
            hits.extend(f"{path.relative_to(root)}:{number}" for number, line in enumerate(lines, 1) if "dev.py" in line)
    assert root / "chupa" / "docs" in visited  # The installed guides must be scanned too.
    assert not hits, "name the `chupa <verb>` the operator runs in backticks; `./dev.py` exists only in the chupa repo\n" + "\n".join(hits)
