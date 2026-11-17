"""Render release notes from squash subjects without changing prior sections."""

import re


def parse_subject(subject: str) -> tuple[str, str] | None:
    match = re.fullmatch(r"clutch\(([^()\s]+)\): (.+)", subject)
    if not match:
        return None
    sentence = re.split(r"(?<=[.!?])\s+", match[2], maxsplit=1)[0]
    return match[1], sentence


def insert_section(existing: str | None, version: str, today: str, subjects: list[str]) -> str:
    section = f"## {version} - {today}\n"
    for subject in subjects:
        parsed = parse_subject(subject)
        if parsed:
            section += f"- {parsed[0]}: {parsed[1]}\n"
    text = existing or "# Changelog\n"
    title, separator, rest = text.partition("\n")
    return title + "\n\n" + section + (rest if separator and rest else "")
