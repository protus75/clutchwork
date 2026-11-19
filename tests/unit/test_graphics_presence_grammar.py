from clutch.tickets import parse_render


def test_presence_grammar():
    prefix = "- mode: generate\n- artifact: output.png\n"
    fields, findings = parse_render(prefix + "- presence: embedding", "ticket.md")
    assert fields["presence"] == ["embedding"] and not findings
    for declaration in ("- presence: orb", "- presence: embedding\n- presence: embedding"):
        _, findings = parse_render(prefix + declaration, "ticket.md")
        assert findings and "presence" in findings[0].message
