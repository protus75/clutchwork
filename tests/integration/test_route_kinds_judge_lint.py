# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that ticket lint requires a review_visual judge route for graphics tickets when implement routes are restricted by kind.
# relates: [tests/integration/test_cli.py, tests/integration/test_lint_verb.py]
# owner: engine
# verified: d32c32ad
# hash: 71c499ceb3477d804a841dc9250c756f2f2bcb3196a8dc28f1e97f64365d4c0f
import pytest

from tests.integration.test_cli import root, ticket, write
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
