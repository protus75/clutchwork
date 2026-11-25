"""Release pre-build commands run before building with a sanitized environment."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks release.pre_build validation, that commands run in order before uv build with a sanitized environment, and that a failure stops build and publish
# relates: [clutch/config.py, clutch/release.py, clutch/runner.py, clutch/seams.py, tests/unit/test_release_publish.py]
# owner: engine
# verified: 403faee1
# hash: b2f501a47112c2615a7cf610afdfc3583328f0cc3842d05c85031c662959d2e0

import pytest
from pydantic import ValidationError

from clutch import config, release
from clutch.runner import Refusal
from clutch.seams import ExecutableNotFound
from tests.unit.test_release_publish import ARTIFACTS, ENV, REPO, SHA, invoke, setup


def test_pre_build_validation():
    assert config.Release().pre_build == []
    assert config.Release(pre_build=[["make", "assets"], ["other"]]).pre_build == [["make", "assets"], ["other"]]
    for invalid in (None, [[]], [[123]]):
        with pytest.raises(ValidationError):
            config.Release(pre_build=invalid)


def test_pre_build_order_and_environment():
    cfg, process, git, fs = setup(True, results=[(0, "", ""), (0, "0.4.0", ""), (0, SHA, ""), (0, SHA, ""), (0, "", ""), (0, "", ""), (0, "", ""), (0, "", "")])
    cfg.release.pre_build = [["first", "asset"], ["second"]]
    original = process.run
    settings = []

    async def run(argv, **kwargs):
        if argv in cfg.release.pre_build:
            settings.append((kwargs["cwd"], kwargs["timeout"]))
        return await original(argv, **kwargs)

    process.run = run
    env = {**ENV, "UV_PUBLISH_TOKEN": "ambient-secret"}
    assert invoke(cfg, process, git, fs, env) == ("0.4.0", ARTIFACTS, True)
    calls = process.calls
    assert [argv for argv, _ in calls] == [
        ["git", "-C", str(REPO), "--no-optional-locks", "status", "--porcelain", "--untracked-files=no"],
        ["uv", "version", "--short"],
        ["git", "-C", str(REPO), "rev-parse", "--verify", "HEAD"],
        ["git", "-C", str(REPO), "rev-parse", "--verify", "refs/tags/v0.4.0^{commit}"],
        ["first", "asset"],
        ["second"],
        ["uv", "build", "--clear", "-o", "/state/dist"],
        ["uv", "publish", *map(str, ARTIFACTS)],
    ]
    assert settings == [(REPO, release.BUILD_TIMEOUT_S), (REPO, release.BUILD_TIMEOUT_S)]
    assert calls[4][1] == calls[5][1] == {"PATH": "/bin"}
    assert calls[-1][1]["UV_PUBLISH_TOKEN"] == "pypi-secret"


@pytest.mark.parametrize("failure", [(3, "", "error"), TimeoutError(), ExecutableNotFound("second")])
def test_pre_build_failure_stops_build_and_upload(failure):
    cfg, process, git, fs = setup(True)
    cfg.release.pre_build = [["first"], ["second"]]
    original = process.run

    async def run(argv, **kwargs):
        if argv == ["second"]:
            process.calls.append((argv, dict(kwargs["env"])))
            if isinstance(failure, Exception):
                raise failure
            return failure
        if argv == ["first"]:
            process.calls.append((argv, dict(kwargs["env"])))
            return (0, "", "")
        return await original(argv, **kwargs)

    process.run = run
    with pytest.raises(Refusal, match="release.pre_build.*second.*fix the pre-build"):
        invoke(cfg, process, git, fs)
    assert [argv for argv, _ in process.calls][-2:] == [["first"], ["second"]]
    assert not any(argv[:2] in (["uv", "build"], ["uv", "publish"]) for argv, _ in process.calls)
