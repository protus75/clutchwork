from clutch.specs import lint_spec
from tests.unit.test_specs import spec_text

SENTENCE = "The first character of your reply is `{` and the last is `}`; no prose, markdown or code fence surrounds the object."


def test_json_output_requires_first_character_instruction():
    text = spec_text().replace(SENTENCE, "")
    findings = lint_spec(text)
    assert any(f.code == "spec_json_reply" and f.paved_road for f in findings)


def test_json_output_accepts_both_first_character_wordings():
    text = spec_text()
    assert lint_spec(text) == []
    assert lint_spec(text.replace("first character", "first non-whitespace character")) == []


def test_non_json_output_does_not_require_first_character_instruction():
    text = spec_text().replace("One JSON object. " + SENTENCE, "Plain text.")
    assert not any(f.code == "spec_json_reply" for f in lint_spec(text))
