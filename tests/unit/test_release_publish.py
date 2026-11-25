"""Publish keeps tagged builds and credentials isolated."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Publish keeps tagged builds and credentials isolated.
# relates: [clutch/__main__.py, clutch/config.py, clutch/git.py, clutch/journal.py, clutch/providers.py, clutch/redact.py, clutch/release.py, clutch/runner.py]
# owner: engine
# verified: 403faee1
# hash: 29f34246ff50807e9fd27b6504b7da8ae5e5e9f1f8edd179fc0d35dc5d7e58be

import asyncio
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch import __main__ as cli
from clutch import config, release
from clutch.git import Git
from clutch.journal import EventType
from clutch.providers import child_env
from clutch.redact import Redactor
from clutch.runner import Refusal
from tests.unit.test_release import REPO, SHA, FakeLock

DIST = Path("/state/dist")
FILES = [".gitignore", "host-0.4.0-py3-none-any.whl", "host-0.4.0.tar.gz"]
ARTIFACTS = [DIST / x for x in FILES[1:]]
ENV = {"PATH": "/bin", "CLAUDE_KEY": "key", "PYPI_TOKEN": "pypi-secret"}


class Exec:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    async def run(self, argv, *, cwd, env, timeout):
        assert cwd == REPO and 0 < timeout < 1000
        self.calls.append((list(argv), dict(env)))
        return self.results.pop(0)


def setup(upload=False, results=None, entries=FILES):
    cfg = NS(state_dir=Path("/state"), release=NS(publish=upload, pypi_token="PYPI_TOKEN", pre_build=[]), providers=[NS(auth="CLAUDE_KEY")])
    process = Exec(results if results is not None else [(0, "", ""), (0, "0.4.0\n", ""), (0, SHA, ""), (0, SHA, ""), (0, "", "")] + ([(0, "", "")] if upload else []))
    git = Git(process, env=child_env(ENV, cfg), timeout=1, commit_lock=FakeLock())
    return cfg, process, git, NS(entries=lambda path: entries)


def invoke(cfg, process, git, fs, env=ENV):
    return asyncio.run(release.publish(REPO, git, process, fs, env, cfg))


def test_publish_uploads_the_tagged_head():
    cfg, process, git, fs = setup(True)
    assert invoke(cfg, process, git, fs) == ("0.4.0", ARTIFACTS, True)
    uv = [argv for argv, env in process.calls if argv[0] == "uv"]
    assert uv == [["uv", "version", "--short"], ["uv", "build", "--clear", "-o", str(DIST)], ["uv", "publish", *map(str, ARTIFACTS)]]
    for argv, env in process.calls:
        assert "--bump" not in argv and "pypi-secret" not in argv
        assert argv[0] != "git" or argv[3] not in ("commit", "tag", "push")
        assert "PYPI_TOKEN" not in env and "CLAUDE_KEY" not in env
        if argv[:2] == ["uv", "publish"]:
            assert env["UV_PUBLISH_TOKEN"] == "pypi-secret"
        else:
            assert "UV_PUBLISH_TOKEN" not in env and "pypi-secret" not in env.values()


def test_publish_false_builds_and_uploads_nothing():
    cfg, process, git, fs = setup()
    assert invoke(cfg, process, git, fs, {"PATH": "/bin"}) == ("0.4.0", ARTIFACTS, False)
    assert [a[:2] for a, _ in process.calls if a[0] == "uv"] == [["uv", "version"], ["uv", "build"]]


@pytest.mark.parametrize("tag", [(128, "", "missing"), (0, "other-sha", "")])
def test_publish_refuses_a_tag_not_on_head(tag):
    cfg, process, git, fs = setup(results=[(0, "", ""), (0, "0.4.0", ""), (0, SHA, ""), tag])
    with pytest.raises(Refusal, match="v0.4.0.*clutch release bump --minor"):
        invoke(cfg, process, git, fs)
    assert not any(a[:2] in (["uv", "build"], ["uv", "publish"]) for a, _ in process.calls)


def test_publish_refuses_dirty_tree_and_missing_token():
    cfg, process, git, fs = setup(results=[(0, " M clutch/core.py\n", "")])
    with pytest.raises(Refusal, match="clutch/core.py"):
        invoke(cfg, process, git, fs)
    assert len(process.calls) == 1
    cfg, process, git, fs = setup(True)
    with pytest.raises(Refusal, match="PYPI_TOKEN.*release.publish: false"):
        invoke(cfg, process, git, fs, {"PATH": "/bin"})
    assert process.calls == []


@pytest.mark.parametrize("case", ["version", "build", "empty", "upload"])
def test_publish_command_failures_refuse(case):
    results = [(0, "", ""), (0, "0.4.0", ""), (0, SHA, ""), (0, SHA, ""), (0, "", ""), (0, "", "")]
    errors = {"version": (1, "error: No project"), "build": (4, "error: build failed"), "upload": (5, "error: 403 Forbidden")}
    if case in errors:
        index, message = errors[case]
        results[index] = (1, "", "warning\n" + message + "\n\n")
    cfg, process, git, fs = setup(case == "upload", results, [".gitignore"] if case == "empty" else FILES)
    with pytest.raises(Refusal) as error:
        invoke(cfg, process, git, fs)
    assert (errors[case][1] if case in errors else "no artifacts") in str(error.value)
    if case != "upload":
        assert not any(a[:2] == ["uv", "publish"] for a, _ in process.calls)


def test_release_token_is_a_configured_secret():
    assert config.Release().model_dump() == {"publish": False, "pypi_token": "UV_PUBLISH_TOKEN", "packages": [], "pre_build": []}
    cfg, _, _, _ = setup()
    env = {"PATH": "/bin", "CLAUDE_KEY": "k", "PYPI_TOKEN": "pypi-secret"}
    assert child_env(env, cfg) == {"PATH": "/bin"}
    assert Redactor.from_config(cfg, env).scrub("x pypi-secret y") == "x [REDACTED:PYPI_TOKEN] y"


@pytest.mark.parametrize("result", [True, False, None])
def test_main_publish_locks_calls_and_prints(monkeypatch, capsys, result):
    events = []
    cfg = NS(state_dir=Path("/state"))
    env = {"PYPI_TOKEN": "pypi-secret"}
    monkeypatch.setattr(cli, "load_config", lambda *a, **kw: cfg)
    monkeypatch.setattr(cli, "child_env", lambda *a: {})

    class Lock:
        def __init__(self, state_dir, *, verb, instance_id, clock):
            assert (state_dir, verb, instance_id) == (Path("/state"), "publish", "description")

        def acquire(self):
            events.append("acquire")

        def release(self):
            events.append("unlock")

    async def describe(self, repo):
        return "description"

    async def publish(repo, git, process, fs, parent, received):
        assert parent == env and received is cfg and repo == REPO
        events.append("publish")
        if result is None:
            raise Refusal("blocked", "repair")
        return "0.4.0", [DIST / "a.whl", DIST / "a.tar.gz"], result

    monkeypatch.setattr(cli, "Lockfile", Lock)
    monkeypatch.setattr(Git, "describe", describe)
    monkeypatch.setattr(release, "publish", publish)
    assert cli.main(["release", "publish"], cwd=REPO, env=env) == (2 if result is None else 0)
    captured = capsys.readouterr()
    assert events == ["acquire", "publish", "unlock"]
    if result is None:
        assert captured.err.startswith("clutch release:") and not captured.out
    else:
        last = "publish: uploaded 0.4.0 to PyPI" if result else "publish: release.publish is false; uploaded nothing -- set release.publish: true in config.yaml to upload"
        assert captured.out.splitlines() == ["publish: built /state/dist/a.whl", "publish: built /state/dist/a.tar.gz", last]


@pytest.mark.parametrize("refuse", [False, True])
def test_main_release_journals_the_release_signal(monkeypatch, refuse):
    events = []
    monkeypatch.setattr(cli, "load_config", lambda *a, **kw: NS(state_dir=Path("/state")))
    monkeypatch.setattr(cli, "child_env", lambda *a: {})

    class Lock:
        def __init__(self, *a, **kw):
            pass

        def acquire(self):
            events.append("acquire")

        def release(self):
            events.append("unlock")

    class Journal:
        def __init__(self, *a):
            pass

        def append(self, *a):
            events.append(a)

    async def describe(self, repo):
        return "description"

    async def bump(*args):
        events.append("release")
        if refuse:
            raise Refusal("blocked", "repair")
        return "0.2.0", SHA

    monkeypatch.setattr(cli, "Lockfile", Lock)
    monkeypatch.setattr(cli, "Journal", Journal)
    monkeypatch.setattr(Git, "describe", describe)
    monkeypatch.setattr(release, "release", bump)
    assert cli.main(["release", "bump", "--minor"], cwd=REPO, env={}) == (2 if refuse else 0)
    expected = [] if refuse else [(EventType.SIGNAL, {"signal": "release", "version": "0.2.0", "tag": "v0.2.0", "commit": SHA})]
    assert events == ["acquire", "release", *expected, "unlock"]
