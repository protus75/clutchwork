# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: conftest
# relates: [tests/fakes.py]
# owner: tests/fakes.py
# verified: d7719818
# hash: 34f67d9dc77cfd42d238217c537880a8faba081a4a6133a9f34e0d8509566c80
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
