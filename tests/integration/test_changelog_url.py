# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test changelog url
# relates: []
# owner: engine
# verified: 148a8874
# hash: aad5c1485193a6c766c726c9670bf3e3af505c56839d744ae66110112d070029
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_project_changelog_url():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert data["project"]["urls"]["Changelog"].endswith("/CHANGELOG.md")
    assert data["project"]["urls"]["Repository"] == "https://github.com/protus75/clutchwork"
