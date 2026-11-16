from pathlib import Path

from clutch.specs import lint_spec

SPECS = Path(__file__).resolve().parents[2] / "clutch" / "specs"
SENTENCE = "The first character of your reply is `{` and the last is `}`; no prose, markdown or code fence surrounds the object."


def test_all_real_specs_lint():
    for path in SPECS.glob("*.md"):
        assert lint_spec(path.read_text()) == [], path.name


def test_removing_author_instruction_is_rejected():
    text = (SPECS / "author.md").read_text()
    assert any(f.code == "spec_json_reply" for f in lint_spec(text.replace(SENTENCE, "")))


def test_new_instructions_are_in_output_sections():
    for name in ("author", "triage", "rework", "retro", "implement"):
        text = (SPECS / f"{name}.md").read_text()
        output = text.split("## Output format\n", 1)[1].split("## On-failure\n", 1)[0]
        assert SENTENCE in output, name
