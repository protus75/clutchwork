import pytest

from chupa.providers import capture_sequence


@pytest.mark.parametrize(
    ("names", "provider", "expected"),
    [
        ([], "claude", 1),
        (["claude-0003", "claude-0001"], "claude", 4),
        (["claude-0005"], "claude", 6),
        (["codex-0009"], "claude", 1),
        (["claude-x", "README", "claude-00010"], "claude", 1),
    ],
)
def test_capture_sequence(names, provider, expected):
    assert capture_sequence(names, provider) == expected
