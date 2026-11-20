"""Exercise publishing through the CLI and real git."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Exercise publishing through the CLI and real git.
# relates: [clutch/__main__.py, clutch/git.py, clutch/journal.py, clutch/lockfile.py, clutch/seams.py, dev.py, tests/integration/test_cli.py]
# owner: engine
# verified: 96e46658
# hash: ca42a60d3a1e8df0f11b2db2b7d3e36003f443b0dcab09bf50306d10b6c627a7

import asyncio
from unittest.mock import Mock

import pytest

import dev
from clutch.__main__ import main
from clutch.git import Git
from clutch.journal import Journal
from clutch.lockfile import CommitLock, Lockfile
from clutch.seams import SubprocessExec
from tests.integration.test_cli import CONFIG, ENV
from tests.integration.test_release import clock, repository  # noqa: F401


@pytest.fixture
def published_repo(tmp_path, monkeypatch):
    git = Git(SubprocessExec(), env=ENV, timeout=10, commit_lock=CommitLock(tmp_path / ".clutch/state", clock=clock, sleep=asyncio.sleep))

    def call(*args):
        return asyncio.run(git._run(tmp_path, *args)).strip()

    asyncio.run(git.init(tmp_path, branch="main"))
    (tmp_path / "config.yaml").write_text(CONFIG + "release: {publish: true, pypi_token: PYPI_TOKEN}\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "host"\nversion = "0.4.0"\n')
    asyncio.run(git.add(tmp_path, ["config.yaml", "pyproject.toml"]))
    asyncio.run(git.commit(tmp_path, "initial"))
    asyncio.run(git.tag(tmp_path, "v0.4.0", "release", call("rev-parse", "HEAD")))
    original = SubprocessExec.run
    calls = []

    async def run(self, argv, **kwargs):
        calls.append((list(argv), dict(kwargs["env"])))
        if argv[0] != "uv":
            return await original(self, argv, **kwargs)
        if argv[1] == "version":
            return 0, "0.4.0\n", ""
        if argv[1] == "build":
            dist = tmp_path / ".clutch/state/dist"
            dist.mkdir(parents=True, exist_ok=True)
            for name in [".gitignore", "host-0.4.0-py3-none-any.whl", "host-0.4.0.tar.gz"]:
                (dist / name).write_text("artifact")
        return 0, "", ""

    monkeypatch.setattr(SubprocessExec, "run", run)
    return tmp_path, git, call, calls


def test_publish_passes_the_token_to_the_upload_only(published_repo, capsys):
    repo, _, call, calls = published_repo
    sha, content = call("rev-parse", "HEAD"), (repo / "pyproject.toml").read_bytes()
    calls.clear()
    assert main(["release", "publish"], cwd=repo, env=ENV | {"PYPI_TOKEN": "pypi-secret"}) == 0
    lines = capsys.readouterr().out.splitlines()
    dist = repo / ".clutch/state/dist"
    assert lines == [f"publish: built {dist}/host-0.4.0-py3-none-any.whl", f"publish: built {dist}/host-0.4.0.tar.gz", "publish: uploaded 0.4.0 to PyPI"]
    assert any(a[0] == "git" for a, _ in calls)
    secret_calls = [(a, e) for a, e in calls if "pypi-secret" in e.values()]
    assert len(secret_calls) == 1 and secret_calls[0][0][:2] == ["uv", "publish"] and secret_calls[0][1]["UV_PUBLISH_TOKEN"] == "pypi-secret"
    assert all("pypi-secret" not in a for a, _ in calls)
    assert call("rev-parse", "HEAD") == sha and (repo / "pyproject.toml").read_bytes() == content
    lock = Lockfile(repo / ".clutch/state", verb="test", instance_id="test", clock=clock)
    lock.acquire()
    lock.release()


def test_publish_without_authorization_reports_artifacts(published_repo, capsys):
    repo, git, call, calls = published_repo
    (repo / "config.yaml").write_text(CONFIG)
    asyncio.run(git.add(repo, ["config.yaml"]))
    asyncio.run(git.commit(repo, "default config"))
    call("tag", "-d", "v0.4.0")
    asyncio.run(git.tag(repo, "v0.4.0", "release", call("rev-parse", "HEAD")))
    calls.clear()
    assert main(["release", "publish"], cwd=repo, env=ENV) == 0
    lines = capsys.readouterr().out.splitlines()
    dist = repo / ".clutch/state/dist"
    assert lines == [
        f"publish: built {dist}/host-0.4.0-py3-none-any.whl",
        f"publish: built {dist}/host-0.4.0.tar.gz",
        "publish: release.publish is false; uploaded nothing -- set release.publish: true in config.yaml to upload",
    ]
    assert all((dist / name).exists() for name in ["host-0.4.0-py3-none-any.whl", "host-0.4.0.tar.gz"])
    assert not any(a[:2] == ["uv", "publish"] for a, _ in calls)


@pytest.mark.parametrize("reason", ["moved", "missing", "lock"])
def test_publish_refusals_change_nothing(published_repo, capsys, reason):
    repo, git, call, calls = published_repo
    lock = Lockfile(repo / ".clutch/state", verb="test", instance_id="test", clock=clock)
    if reason == "moved":
        (repo / "extra").write_text("later")
        asyncio.run(git.add(repo, ["extra"]))
        asyncio.run(git.commit(repo, "later"))
    elif reason == "missing":
        call("tag", "-d", "v0.4.0")
    else:
        lock.acquire()
    before = (call("rev-parse", "HEAD"), call("tag", "--list"))
    calls.clear()
    try:
        assert main(["release", "publish"], cwd=repo, env=ENV | {"PYPI_TOKEN": "pypi-secret"}) == 2
    finally:
        if lock.held:
            lock.release()
    err = capsys.readouterr().err
    assert err.startswith("clutch release:")
    if reason == "lock":
        assert "clutch.lock" in err and not any(a[0] == "uv" for a, _ in calls)
    else:
        assert "v0.4.0" in err and "clutch release bump --minor" in err
        assert not any(a[:2] in (["uv", "build"], ["uv", "publish"]) for a, _ in calls)
    assert (call("rev-parse", "HEAD"), call("tag", "--list")) == before


def test_release_journals_the_release_signal(repository):
    repo, _, call, _ = repository
    assert main(["release", "bump", "--minor"], cwd=repo, env=ENV) == 0
    signals = [e for e in Journal(repo / ".clutch/state", clock).read() if e.type == "signal"]
    assert [e.body for e in signals] == [{"signal": "release", "version": "0.2.0", "tag": "v0.2.0", "commit": call("rev-parse", "HEAD")}]


def test_dev_publish_is_removed(monkeypatch):
    monkeypatch.setattr(dev.sys, "argv", ["dev.py", "publish"])
    run = Mock()
    monkeypatch.setattr(dev.subprocess, "run", run)
    with pytest.raises(SystemExit) as error:
        dev.main()
    assert error.value.code == 2
    run.assert_not_called()
