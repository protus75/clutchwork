# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test training config
# relates: [clutch/config.py]
# owner: clutch/config.py
# verified: 9a610809
# hash: 9e47129e66e49ef8df2745a647194057fc5d56d70553138429b1083692363c54
import pytest
from pydantic import ValidationError

from clutch.config import Config, TrainingData


def test_defaults():
    assert Config.model_fields["training_data"].default == TrainingData()
    assert TrainingData().enabled is False
    assert TrainingData().exclude == []


def test_effective_exclude():
    assert TrainingData(exclude=["data/customers/**"]).effective_exclude() == [".env*", "*.pem", "*.key", "id_*", "data/customers/**"]
    assert TrainingData(exclude=[".env*", "extra", "extra"]).effective_exclude() == [".env*", "*.pem", "*.key", "id_*", "extra"]


def test_require_enabled():
    with pytest.raises(ValueError, match="training_data.enabled: true"):
        TrainingData().require_enabled()
    assert TrainingData(enabled=True).require_enabled() is None


def test_invalid_fields():
    with pytest.raises(ValidationError):
        TrainingData(unknown=1)
    with pytest.raises(ValidationError):
        TrainingData(exclude=[""])
