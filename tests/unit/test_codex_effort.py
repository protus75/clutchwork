# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test codex effort
# relates: [clutch/providers.py]
# owner: clutch/providers.py
# verified: 0a308920
# hash: 14d68076751de40d507be385af26e602bfc78817511d9bf6d84808ae999fce32
import pytest

from clutch.providers import CodexAdapter


def test_codex_max_effort():
    adapter = CodexAdapter.__new__(CodexAdapter)
    argv = CodexAdapter.argv(adapter, "model", "max", False)
    assert "model_reasoning_effort=high" in argv
    assert "model_reasoning_effort=max" not in argv
    with pytest.raises(KeyError):
        CodexAdapter.argv(adapter, "model", "unknown", False)
