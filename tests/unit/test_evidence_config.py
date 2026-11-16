import pytest
from pydantic import ValidationError

from clutch.config import Config, Evidence


def test_evidence_defaults():
    assert Evidence().max_gb == 20
    assert Config.model_fields["evidence"].default == Evidence()
    with pytest.raises(ValidationError):
        Evidence(max_gb=0)
