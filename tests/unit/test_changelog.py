# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test changelog
# relates: [clutch/changelog.py]
# owner: clutch/changelog.py
# verified: 0a308920
# hash: 88bbd178a8c4e4da8e5bc785708b94bf7f33faa6da99534bcdcede9a56639214
from clutch.changelog import insert_section, parse_subject


def test_parse_subject_and_skip_non_squash():
    assert parse_subject("clutch(a-b): Does X. Also Y.") == ("a-b", "Does X.")
    assert parse_subject("ordinary commit") is None


def test_insert_preserves_previous_section():
    old = "# Changelog\n\n## 0.3.0 - 2026-01-01\n- old: Previous.\n\n  unchanged\n"
    result = insert_section(old, "0.4.0", "2026-02-03", ["clutch(a-b): Does X. Also Y.", "other"])
    assert result == "# Changelog\n\n## 0.4.0 - 2026-02-03\n- a-b: Does X.\n\n" + old[old.index("## 0.3.0") :]
    assert result[result.index("## 0.3.0") :] == old[old.index("## 0.3.0") :]


def test_empty_and_missing_changelog_without_tickets():
    for old in (None, ""):
        assert insert_section(old, "0.4.0", "2026-02-03", []) == "# Changelog\n\n## 0.4.0 - 2026-02-03\n"
