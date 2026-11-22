# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the Evidence config defaults: warn_gb is 20, a zero threshold is refused, and the removed max_gb field is refused
# relates: [clutch/config.py]
# owner: clutch/config.py
# verified: 2036efdf
# hash: 1e70ceccdebcffb49c6ffb261980153d12d905688d53f854a052f46a4e17f68a
import pytest
from pydantic import ValidationError

from clutch.config import Config, Evidence


def test_evidence_defaults():
    assert Evidence().warn_gb == 20
    assert Config.model_fields["evidence"].default == Evidence()
    with pytest.raises(ValidationError):
        Evidence(warn_gb=0)
    with pytest.raises(ValidationError):
        Evidence(max_gb=20)
