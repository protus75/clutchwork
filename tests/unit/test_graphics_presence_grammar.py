# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test graphics presence grammar
# relates: [clutch/tickets.py]
# owner: clutch/tickets.py
# verified: 0a308920
# hash: d420c30b05a7d229da069140c17317373c7919821df8a111dad22d352a0988cc
from clutch.tickets import parse_render


def test_presence_grammar():
    prefix = "- mode: generate\n- artifact: output.png\n"
    fields, findings = parse_render(prefix + "- presence: embedding", "ticket.md")
    assert fields["presence"] == ["embedding"] and not findings
    for declaration in ("- presence: orb", "- presence: embedding\n- presence: embedding"):
        _, findings = parse_render(prefix + declaration, "ticket.md")
        assert findings and "presence" in findings[0].message
