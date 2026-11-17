import tomllib
from pathlib import Path


def test_project_changelog_url():
    data = tomllib.loads(Path("pyproject.toml").read_text())
    assert data["project"]["urls"]["Changelog"].endswith("/CHANGELOG.md")
    assert data["project"]["urls"]["Repository"] == "https://github.com/protus75/clutchwork"
