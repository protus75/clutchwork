# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test gate floors
# relates: []
# owner: engine
# verified: 148a8874
# hash: 63ce1d64e64bbfe2892f5a3fbda568a379df1dec694d359aafcdcf948ee4ba6a
import tomllib
from pathlib import Path


def test_coverage_floors():
    text = (Path(__file__).resolve().parents[2] / "test-gate.toml").read_text()
    floors = tomllib.loads(text)["coverage"]["files"]

    # Missing entries and lowered floors must fail instead of inheriting a default.
    for name, minimum in {
        "graph": 90,
        "audit": 1,
        "observe": 1,
        "seams": 1,
        "stats": 1,
        "thresh": 1,
        "watchdog": 1,
        "__main__": 13,
        "redact": 50,
        "gates": 38,
    }.items():
        assert floors.get(f"clutch/{name}.py", -1) >= minimum, name

    for name in ("covmap", "doctor"):
        # Missing or raised entries must not silently inherit the default floor.
        assert floors.get(f"clutch/{name}.py") == 0, name
        line = next(line for line in text.splitlines() if line.startswith(f'"clutch/{name}.py"'))
        # A comment on another entry must not explain this module's zero floor.
        assert "integration" in line.partition("#")[2].lower(), name
