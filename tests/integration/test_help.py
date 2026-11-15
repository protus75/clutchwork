"""Check registry links and vocabulary against shipped inputs."""

import json
import re
from importlib.metadata import metadata
from pathlib import Path
from urllib.parse import urlsplit

import clutch
from clutch.help import COMMANDS, TOPICS, help_map

ROOT = Path(__file__).resolve().parents[2]


def registry():
    urls = metadata("clutchwork").get_all("Project-URL")
    repo = next(value.split(",", 1)[1].strip() for value in urls if value.split(",", 1)[0].strip() == "Repository")
    return help_map(Path.read_text, repo), repo


def test_links_resolve():
    result, repo = registry()
    for key, entry in result.items():
        link = entry["link"]
        if "path" in link:
            path = Path(link["path"])
            assert path.is_relative_to(Path(clutch.__file__).parent / "docs")
            line = path.read_text().splitlines()[link["line"]]
            if key.startswith("verb."):
                assert line.startswith(f"| `{key[5:]}` |")
            else:
                assert re.fullmatch(r"#+\s+" + re.escape(TOPICS[key]["heading"]), line)
        else:
            assert link["url"].startswith(repo.rstrip("/") + "/blob/main/")
            relative = link["url"].split("/blob/main/", 1)[1]
            path, fragment = relative.split("#", 1)
            headings = re.findall(r"^#+\s+(.+)$", (ROOT / path).read_text(), re.M)
            slugs = [re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-") for heading in headings]
            assert fragment in slugs


def test_manifest_covered():
    package = json.loads((ROOT / "vscode-clutchwork/package.json").read_text())
    manifest = package["contributes"]
    assert {row["command"] for row in manifest["commands"]} == COMMANDS.keys()
    assert set(COMMANDS.values()) <= TOPICS.keys()
    views = {row["id"] for row in manifest["views"]["clutch"]}
    assert {"view." + view for view in views} <= TOPICS.keys()
    menus = manifest["menus"]["view/title"]
    assert all(any(item["command"] == "clutch.help" and item["when"] == f"view == {view}" and item.get("group") != "navigation" for item in menus) for view in views)
    repo = package["repository"]["url"].removesuffix(".git").rstrip("/")
    for setting in manifest["configuration"]["properties"].values():
        assert "description" not in setting
        description = setting["markdownDescription"]
        assert "Before:" in description and "After:" in description
        links = re.findall(r"\]\((https://[^)]+)\)", description)
        assert len(links) == 1 and links[0].startswith(repo + "/blob/main/")
        path, fragment = links[0].split("/blob/main/", 1)[1].split("#", 1)
        headings = re.findall(r"^#+\s+(.+)$", (ROOT / path).read_text(), re.M)
        assert fragment in [re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-") for heading in headings]


def test_verb_what_from_run_guide():
    result, _ = registry()
    lines = (Path(clutch.__file__).parent / "docs/host-running.md").read_text().splitlines()
    for key in TOPICS:
        if key.startswith("verb."):
            row = next(line for line in lines if line.startswith(f"| `{key[5:]}` |"))
            assert result[key]["what"] == row.split("|")[3].strip().replace("`", "")
