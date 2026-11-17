import pytest

from tests.fakes import FakeClock, FakeExec, FakeFileSystem, FakeGit, FakeJournal


@pytest.fixture
def fake_clock():
    return FakeClock()


@pytest.fixture
def fake_exec():
    return FakeExec()


@pytest.fixture
def fake_fs():
    return FakeFileSystem()


@pytest.fixture
def fake_journal():
    return FakeJournal()


@pytest.fixture
def fake_git():
    return FakeGit()
