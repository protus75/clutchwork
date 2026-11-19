import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_project_changelog_url():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert data["project"]["urls"]["Changelog"].endswith("/CHANGELOG.md")
    assert data["project"]["urls"]["Repository"] == "https://github.com/protus75/clutchwork"
