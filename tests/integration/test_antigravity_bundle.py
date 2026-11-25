"""The committed portable plugin agrees with its source."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose:
# relates: [clutch/antigravity.py]
# owner: clutch/antigravity.py
# verified: 8342251d
# hash: 693d3407579930bd9f55cc2e697a8700cdc75a7404deab4b2dd2b4f422217cfd

import tomllib
from pathlib import Path

from clutch.antigravity import portable_bundle_files

ROOT = Path(__file__).resolve().parents[2]


def test_committed_bundle():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    logo = (ROOT / "clutch/assets/logo.svg").read_bytes()
    for path, expected in portable_bundle_files(version_str=version, logo_bytes=logo).items():
        assert (ROOT / path).read_bytes() == expected, path
    assert {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()} == {"clutch-drain-loop", "clutch-plan-drain", "clutch-plan-serve"}


def test_readme_install_and_validation():
    section = (ROOT / "README.md").read_text().split("## Antigravity plugin\n", 1)[1].split("\n## ", 1)[0]
    assert "agy plugin install https://github.com/protus75/clutchwork" in section
    assert "agy plugin validate --strict ." in section
