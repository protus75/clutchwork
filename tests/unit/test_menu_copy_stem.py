"""Copy Stem is available only in the merged section."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the extension-only Copy Stem menu entry is admitted and shown only for rows in the merged section
# relates: [clutch/observe.py]
# owner: clutch/observe.py
# verified: 322b4db9
# hash: e2411e1656f6d8e9c53278d77331af29e1100bc12a0109902ab5227f44ad5c99

import pytest

from clutch import observe


@pytest.mark.parametrize(
    "section,outcome,visibility",
    [("merged", "admit", "on"), ("queued", "noop", "off"), ("running", "noop", "off"), ("blocked", "noop", "off")],
)
def test_copy_stem_admission_and_menu(monkeypatch, section, outcome, visibility):
    entry = observe.MENU["clutchCopyStem"]
    assert entry.admission(section=section).outcome == outcome
    monkeypatch.setattr(observe, "MENU", {"clutchCopyStem": entry})
    assert observe.row_menu("ticket", {"clutchCopyStem": {"section": section}}, False)["clutchCopyStem"] == visibility
