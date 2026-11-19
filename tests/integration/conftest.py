import pytest


@pytest.fixture(autouse=True)
def isolate_working_directory(monkeypatch, tmp_path_factory):
    """Use an explicit fixture repo (e.g. main([...], cwd=repo) or watch_fixture_repo), or anchor tracked reads on Path(__file__).resolve().parents[2]."""
    monkeypatch.chdir(tmp_path_factory.mktemp("integration-cwd"))
