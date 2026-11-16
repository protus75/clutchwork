from pathlib import Path


def test_diagnose_requires_bare_json_in_output_format():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/diagnose.md").read_text()
    task = text.split("## Task\n", 1)[1].split("## Inputs\n", 1)[0]
    output = text.split("## Output format\n", 1)[1].split("## On-failure\n", 1)[0]
    on_failure = text.split("## On-failure\n", 1)[1]
    # Omitting a clause or placing it in another section leaves output instructions incomplete.
    for clause in (
        "The first character of your reply is `{` and the last is `}`",
        "no prose, markdown or code fence surrounds the object",
        "reasoning goes in the lessons",
    ):
        assert clause in output
        assert clause not in task
        assert clause not in on_failure
