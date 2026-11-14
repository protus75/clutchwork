"""Check registry links and vocabulary against shipped inputs."""

import json
import re
from importlib.metadata import metadata
from pathlib import Path
from urllib.parse import urlsplit

import chupa
from chupa.help import COMMANDS, TOPICS, help_map

ROOT = Path(__file__).resolve().parents[2]


def registry():
    urls = metadata("chupa").get_all("Project-URL")
    repo = next(value.split(",", 1)[1].strip() for value in urls if value.split(",", 1)[0].strip() == "Repository")
    return help_map(Path.read_text, repo), repo


def test_links_resolve():
    result, repo = registry()
    for key, entry in result.items():
        link = entry["link"]
        if "path" in link:
            path = Path(link["path"])
            assert path.is_relative_to(Path(chupa.__file__).parent / "docs")
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
    manifest = json.loads((ROOT / "vscode-chupa/package.json").read_text())["contributes"]
    assert {row["command"] for row in manifest["commands"]} == COMMANDS.keys()
    assert set(COMMANDS.values()) <= TOPICS.keys()
    assert {"view." + row["id"] for row in manifest["views"]["chupa"]} <= TOPICS.keys()


def test_verb_what_from_run_guide():
    result, _ = registry()
    lines = (Path(chupa.__file__).parent / "docs/host-running.md").read_text().splitlines()
    for key in TOPICS:
        if key.startswith("verb."):
            row = next(line for line in lines if line.startswith(f"| `{key[5:]}` |"))
            assert result[key]["what"] == row.split("|")[3].strip().replace("`", "")
