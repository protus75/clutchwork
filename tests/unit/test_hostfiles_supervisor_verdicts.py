from clutch.hostfiles import CORE_TEMPLATE


def test_supervisor_recommendations_and_template_budget():
    rule = next(line for line in CORE_TEMPLATE.splitlines() if line.startswith(b"- A supervising session"))
    assert b"may not confirm or reject" not in CORE_TEMPLATE
    assert b"rewrite a ticket the engine authored" not in CORE_TEMPLATE
    assert b"clutch prompt diagnose" in rule
    assert b"clutch prompt drafts" in rule
    assert b"Recommendation" in rule
    assert len(CORE_TEMPLATE) <= 8192
