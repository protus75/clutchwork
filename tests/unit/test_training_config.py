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
