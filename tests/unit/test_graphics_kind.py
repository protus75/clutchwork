import pytest

from clutch import tickets


def source(render, *, kind="graphics", goal="A prompt", criteria="1. Run `check`.", fence="tests/render"):
    return f"""---
state: confirmed
source: human
priority: P2
kind: {kind}
---
## Depends on
none
## Context
- context.txt
## Goal / Why
{goal}
## Boundary contract
none
- reason: no boundary
## Scope in / Scope out
Visual work.
## Scope fence
- {fence}
## Acceptance criteria
{criteria}
## Verification
```
check
```
## Definition of rejected
Wrong output.
## Time budget
- expected: 10m
- stuck: 20m
{render}
"""


GENERATE = "## Render\n- mode: generate\n- artifact: assets/hero.png\n- input: tickets/hero/reference/product.png\n- candidates: 3"
COMMAND = "## Render\n```\nuv run python tests/render/home.py\n```\n- mode: command\n- artifact: .clutch/render/home.png\n- carries: tests/render"


def parse(tmp_path, text):
    (tmp_path / "context.txt").write_text("context")
    return tickets.validate_ticket("hero", text, tmp_path)


def lint(tmp_path, text):
    return [f.message for f in tickets.lint_findings(parse(tmp_path, text), tmp_path)]


def test_kind_and_templates():
    assert tickets.KINDS == ("feature", "bug", "chore", "graphics")
    assert "## Render" in tickets.template("graphics")
    assert "## Render" not in tickets.template("feature")


def test_generate_and_invalid_fields(tmp_path):
    assert not lint(tmp_path, source(GENERATE))
    for broken in [GENERATE.replace("generate", "other"), GENERATE.replace("candidates: 3", "candidates: 0"), GENERATE.replace("candidates: 3", "candidates: 6")]:
        with pytest.raises(tickets.TicketInvalid):
            parse(tmp_path, source(broken))


def test_section_by_kind(tmp_path):
    for text in (source(GENERATE, kind="feature"), source("")):
        with pytest.raises(tickets.TicketInvalid):
            parse(tmp_path, text)


def test_command_rules(tmp_path):
    assert not lint(tmp_path, source(COMMAND))
    for broken in [
        COMMAND.replace("uv run python tests/render/home.py", ""),
        COMMAND.replace("uv run python tests/render/home.py", "uv run python tests/render/home.py\nother command"),
        COMMAND.replace("- carries: tests/render", ""),
        COMMAND + "\n- input: file.png",
        COMMAND + "\n- candidates: 3",
    ]:
        with pytest.raises(tickets.TicketInvalid):
            parse(tmp_path, source(broken))
    assert any("carried file" in m for m in lint(tmp_path, source(COMMAND.replace("tests/render/home.py", "scripts/home.py"))))
    assert any("outside" in m for m in lint(tmp_path, source(COMMAND, fence="other")))
    with pytest.raises(tickets.TicketInvalid, match="Goal / Why"):
        parse(tmp_path, source(COMMAND, goal=""))


def test_visual_and_mechanical(tmp_path):
    visual = "- visual: assets/hero.png: product sits at left third"
    mechanical = "1. Run `check`."
    assert not lint(tmp_path, source(GENERATE, criteria=visual + "\n" + mechanical))
    assert any("undeclared" in m for m in lint(tmp_path, source(GENERATE, criteria=visual.replace("assets/hero.png", "other.png") + "\n" + mechanical)))
    assert any("mechanical" in m for m in lint(tmp_path, source(GENERATE, criteria=visual)))
    with pytest.raises(tickets.TicketInvalid, match="names no check"):
        parse(tmp_path, source("", kind="feature", criteria=visual))


def test_generate_input_or_prompt(tmp_path):
    no_input = GENERATE.replace("- input: tickets/hero/reference/product.png\n", "")
    assert any("no input or prompt" in m for m in lint(tmp_path, source(no_input, goal="")))
    assert not lint(tmp_path, source(GENERATE, goal=""))
    assert not lint(tmp_path, source(no_input, goal="Draw a product"))
    assert any("three inputs" in m for m in lint(tmp_path, source(GENERATE + "\n- input: a.png\n- input: b.png\n- input: c.png")))
