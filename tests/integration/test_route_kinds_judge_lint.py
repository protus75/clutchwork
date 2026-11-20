# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test route kinds judge lint
# relates: [tests/integration/test_cli.py, tests/integration/test_lint_verb.py]
# owner: engine
# verified: 96e46658
# hash: 9c48371f56e6c46fb3453ab3dc2c35d35bc9f31292ddd1ba532b642c491ea0c9
from tests.integration.test_cli import root, ticket, write
from tests.integration.test_lint_verb import lint


def test_graphics_judge_lint(root, capsys):
    path = root / "config.yaml"
    original = path.read_text()
    original = original.replace("surface: implement, candidates:", "surface: implement, kinds: [graphics], candidates:")
    original = original.replace("review: {}", "  - {tier: medium, surface: review, candidates: [{provider: claude}]}\nreview: {}")
    path.write_text(original)
    graphics = ticket().replace("kind: feature", "kind: graphics") + "\n## Render\n- mode: generate\n- artifact: assets/hero.png\n- candidates: 3\n"
    write(root, "example", graphics)
    assert lint(root, "example") == 1
    assert "review_visual" in capsys.readouterr().out
    path.write_text(original.replace("surface: review, candidates: [{provider: claude}]", "surface: review, candidates: [{provider: claude, model: judge}]"))
    assert lint(root, "example") == 0
    path.write_text(original)
    write(root, "example", ticket())
    assert lint(root, "example") == 0
