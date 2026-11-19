from clutch import roadmap
from tests.unit.test_roadmap_status import HEADER, row


def choose(*lines, states=None):
    return roadmap.choose(roadmap.parse("".join(lines)), states=states or {}, files=set())


def table(*rows, release="0.4.0"):
    return f"### {release}\n" + HEADER + "".join(rows)


def assert_ready(choice, stem):
    assert stem in [item.stem for item in choice.ready]
    assert stem not in [wait.row.stem for wait in choice.waits]


def assert_held(choice, stem, release="0.4.0", count=1):
    assert stem not in [item.stem for item in choice.ready]
    assert [(wait.reason, wait.road) for wait in choice.waits if wait.row.stem == stem] == [(f"release {release} has {count} open rows", "merge or strike the other rows of the release")]


def test_audit_waits_while_sibling_open():
    choice = choose(table(row(1, "release-audit-040"), row(2, "sibling")))
    assert_held(choice, "release-audit-040")


def test_audit_ready_when_siblings_struck():
    choice = choose(table(row(1, "release-audit-040"), row(2, "sibling", struck=True)))
    assert_ready(choice, "release-audit-040")


def test_audit_ready_when_siblings_settled():
    choice = choose(table(row(1, "release-audit-040"), row(2, "sibling")), states={"sibling": "merged"})
    assert_ready(choice, "release-audit-040")


def test_other_release_does_not_block():
    choice = choose(table(row(1, "release-audit-040")), table(row(2, "sibling"), release="0.5.0"))
    assert_ready(choice, "release-audit-040")


def test_refile_stem_is_audit_row():
    choice = choose(table(row(1, "release-audit-040-r1"), row(2, "sibling")))
    assert_held(choice, "release-audit-040-r1")


def test_ordinary_row_unaffected():
    choice = choose(table(row(1, "ordinary"), row(2, "sibling")))
    assert_ready(choice, "ordinary")


def test_audit_stem_follows_release():
    choice = choose(table(row(1, "release-audit-050"), row(2, "release-audit-040"), release="0.5.0"))
    assert_held(choice, "release-audit-050", release="0.5.0")
    assert_ready(choice, "release-audit-040")


def test_linked_audit_row_unaffected():
    choice = choose(table(row(1, "release-audit-040", "`tickets/release-audit-040/`"), row(2, "sibling")))
    assert choice.open == 1
    assert "release-audit-040" not in [wait.row.stem for wait in choice.waits]


def test_audit_depends_checked_first():
    text = table(row(1, "release-audit-040", depends="`dependency`"), row(2, "dependency"), row(3, "sibling"))
    choice = choose(text)
    assert "release-audit-040" not in [item.stem for item in choice.ready]
    assert "release-audit-040" not in [wait.row.stem for wait in choice.waits]
    assert_held(choose(text, states={"dependency": "merged"}), "release-audit-040")
