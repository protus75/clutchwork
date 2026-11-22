# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that the shared SPECS test constant points to the shipped implement prompt spec
# relates: [tests/stages_helpers.py]
# owner: tests/stages_helpers.py
# verified: 0a4d026b
# hash: f21bbfbf3344f3c3f3536fdf337040decf0db4f6f2f3f74cba71b1a83409252f
from tests.stages_helpers import SPECS


def test_specs_points_to_shipped_implement_spec():
    assert (SPECS / "implement.md").read_text().startswith("---\nllm_surface: implement\n")
