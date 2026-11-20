# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test release packages
# relates: [clutch/release.py, clutch/seams.py]
# owner: engine
# verified: 9a610809
# hash: 8ce1e0b9dd1dae74103e04b08aebd677db46dedc50708729e32b62320cf3da53
import asyncio
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch.release import BUILD_TIMEOUT_S, run_packages
from clutch.seams import ExecutableNotFound

REPO = Path("/repo")
PATTERN = "dist/vscode-clutchwork-*.vsix"


def invoke(before, after, result=(0, "", "")):
    calls = []
    entries = iter([before, after])

    class FS:
        def entries(self, path):
            assert path == REPO / "dist"
            return next(entries)

    class Exec:
        async def run(self, argv, *, cwd, env, timeout):
            calls.append((argv, cwd, env, timeout))
            if isinstance(result, Exception):
                raise result
            return result

    cfg = NS(release=NS(packages=[NS(argv=["pack", "arg"], kept=PATTERN)], pypi_token="TOKEN"), providers=[NS(auth="KEY")])
    lines = asyncio.run(run_packages(REPO, Exec(), FS(), {"PATH": "/bin", "KEY": "secret", "TOKEN": "token"}, cfg))
    return lines, calls


def test_new_matches_and_sanitized_command():
    lines, calls = invoke(["vscode-clutchwork-0.2.7.vsix"], ["vscode-clutchwork-0.2.7.vsix", "vscode-clutchwork-0.2.8.vsix", "other.txt"])
    assert lines == ["package: kept dist/vscode-clutchwork-0.2.8.vsix"]
    assert calls == [(["pack", "arg"], REPO, {"PATH": "/bin"}, BUILD_TIMEOUT_S)]


@pytest.mark.parametrize("before,after", [([], []), (["vscode-clutchwork-0.2.7.vsix"], ["vscode-clutchwork-0.2.7.vsix"])])
def test_nothing_new(before, after):
    assert invoke(before, after)[0] == [f"package: nothing kept for {PATTERN}"]


@pytest.mark.parametrize("result,expected", [((1, "", ""), "rc 1"), (TimeoutError(), "timeout"), (ExecutableNotFound("pack"), "not found"), (OSError(), "OSError")])
def test_failures_are_digest_lines(result, expected):
    assert invoke([], [], result)[0] == [f"package: pack failed ({expected})"]


def test_empty_packages_needs_no_seams_or_providers():
    assert asyncio.run(run_packages(REPO, object(), object(), {"PATH": "/bin"}, NS(release=NS(packages=[])))) == []
