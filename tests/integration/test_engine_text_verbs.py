"""Engine text must name host-accessible operator verbs."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Engine text must name host-accessible operator verbs.
# relates: []
# owner: engine
# verified: d6f7e6b4
# hash: 31a910cce1d8fb7a407d9f0fcb579453c5df0d3f81f713e203060970498aed56

import os
from pathlib import Path


def test_no_engine_text_names_dev_py():
    root = Path(__file__).resolve().parents[2]
    hits = []
    visited = set()
    for directory, dirs, files in os.walk(root / "clutch"):
        visited.add(Path(directory))
        dirs[:] = [name for name in dirs if name != "__pycache__"]
        for name in files:
            path = Path(directory, name)
            if path == root / "clutch" / "assets" / "logo.png":
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError as error:
                raise AssertionError(f"{path.relative_to(root)} is not UTF-8; prune it deliberately") from error
            hits.extend(f"{path.relative_to(root)}:{number}" for number, line in enumerate(lines, 1) if "dev.py" in line)
    assert root / "clutch" / "docs" in visited  # The installed guides must be scanned too.
    assert not hits, "name the `clutch <verb>` the operator runs in backticks; `./dev.py` exists only in the clutch repo\n" + "\n".join(hits)
