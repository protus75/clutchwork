# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test training config
# relates: [clutch/config.py]
# owner: clutch/config.py
# verified: f11f41cf
# hash: 69087dfc518e6f10018785bcdfff86e78ba25fe15696e0045ee73bf13eb934c5
import pytest
from pydantic import ValidationError

from clutch.config import Config, TrainingData, snapshot_config, training_exclude


def test_defaults():
    assert Config.model_fields["training_data"].default == TrainingData()
    assert TrainingData().enabled is False
    assert TrainingData().exclude == []


def test_training_exclude():
    assert training_exclude(TrainingData(exclude=["data/customers/**"])) == [".env*", "*.pem", "*.key", "id_*", "data/customers/**"]
    assert training_exclude(TrainingData(exclude=[".env*", "extra", "extra"])) == [".env*", "*.pem", "*.key", "id_*", "extra"]


def test_require_enabled():
    with pytest.raises(ValueError, match="training_data.enabled: true"):
        TrainingData().require_enabled()
    assert TrainingData(enabled=True).require_enabled() is None


def test_invalid_fields():
    with pytest.raises(ValidationError):
        TrainingData(unknown=1)
    with pytest.raises(ValidationError):
        TrainingData(exclude=[""])


def test_training_exclude_reads_a_config_snapshot():
    # Serve passes stages snapshot_config(...), which keeps fields but drops model methods.
    snapshot = snapshot_config(TrainingData(enabled=True, exclude=["extra"]))
    assert not hasattr(snapshot, "effective_exclude")
    assert training_exclude(snapshot) == [".env*", "*.pem", "*.key", "id_*", "extra"]
