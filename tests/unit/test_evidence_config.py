# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test evidence config
# relates: [clutch/config.py]
# owner: clutch/config.py
# verified: 0a308920
# hash: 36bb0950dd912a12abc7701f9e40abc1ad64a85c8ade188f83881001375ebd45
import pytest
from pydantic import ValidationError

from clutch.config import Config, Evidence


def test_evidence_defaults():
    assert Evidence().max_gb == 20
    assert Config.model_fields["evidence"].default == Evidence()
    with pytest.raises(ValidationError):
        Evidence(max_gb=0)
