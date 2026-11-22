# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that ticket lint requires a review_visual judge route for graphics tickets when implement routes are restricted by kind
# relates: [tests/integration/test_cli.py, tests/integration/test_lint_verb.py]
# owner: engine
# verified: ae1a5a3b
# hash: b4a7abfddee4cb373ef387f6f4eb5b1f6fb07a44486e5250fb0103e5f1129554
import pytest

from tests.cli_helpers import root, ticket, write
from tests.integration.test_lint_verb import lint

pytestmark = pytest.mark.disk_io_skip


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
