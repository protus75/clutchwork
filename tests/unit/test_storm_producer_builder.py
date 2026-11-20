# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test storm producer builder
# relates: [clutch/daemon.py]
# owner: clutch/daemon.py
# verified: 9a610809
# hash: 1af2755c529396772317e3b21ee3309cbaaf91aa1743ff89e72221f3463a5973
from types import SimpleNamespace
from unittest.mock import Mock

from clutch import daemon


def test_builder_composes_box_at_configured_root(tmp_path):
    fs, journal, clock = Mock(), Mock(), Mock()
    box = daemon.storm_producer_for_config(SimpleNamespace(state_dir=tmp_path), fs=fs, journal=journal, clock=clock)

    assert box.root == tmp_path / "box"
    assert box.fs is fs


def test_builder_forwards_dependencies_to_composer(tmp_path, monkeypatch):
    fs, journal, clock = Mock(), Mock(), Mock()
    composer = Mock(return_value=object())
    monkeypatch.setattr(daemon, "storm_producer", composer)

    result = daemon.storm_producer_for_config(SimpleNamespace(state_dir=tmp_path), fs=fs, journal=journal, clock=clock)

    assert result is composer.return_value
    composer.assert_called_once_with(root=tmp_path / "box", fs=fs, journal=journal, clock=clock)
