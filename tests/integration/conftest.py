# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: conftest
# relates: []
# owner: engine
# verified: 148a8874
# hash: e2d7759b6fb3841a3514e0e12950a4cf223f4f9350878d0abd2683fecddeb080
import pytest


@pytest.fixture(autouse=True)
def isolate_working_directory(monkeypatch, tmp_path_factory):
    """Use an explicit fixture repo (e.g. main([...], cwd=repo) or watch_fixture_repo), or anchor tracked reads on Path(__file__).resolve().parents[2]."""
    monkeypatch.chdir(tmp_path_factory.mktemp("integration-cwd"))
