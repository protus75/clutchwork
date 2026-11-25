# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that CORE_TEMPLATE has exactly one clutch:meta retrieval rule under Engine conduct, that the rule contains its required phrases, and that the template stays within 8192 bytes.
# relates: [clutch/hostfiles.py]
# owner: clutch/hostfiles.py
# verified: 5fb36345
# hash: 83d705b74935a67144362ebbfede75a323954db4297bf48ab638e2c7a7ad7799
from clutch.hostfiles import CORE_TEMPLATE


def test_meta_retrieval_rule_and_template_budget():
    lines = CORE_TEMPLATE.splitlines()
    matches = [i for i, line in enumerate(lines) if line.startswith(b"- ") and b"clutch:meta" in line]
    assert len(matches) == 1
    engine = lines.index(b"## Engine conduct")
    assert matches[0] > engine
    assert not any(line.startswith(b"## ") for line in lines[engine + 1 : matches[0]])
    rule = lines[matches[0]]
    for phrase in (
        b"`purpose`",
        b"`relates`",
        b"`owner`",
        b"routing hints",
        b"read the owning file before editing or citing",
        b"`clutch meta check`",
        b"staleness is suspected",
        b"`clutch context suggest <stem>` on drafts",
        b"Never hand-edit `clutch:meta` blocks",
        b"`clutch meta refresh` / Check owns them",
    ):
        assert phrase in rule
    assert len(CORE_TEMPLATE) <= 8192
