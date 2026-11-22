"""Exercise the plugin in pytest sessions, including the xdist controller."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Runs the clutch.testguard pytest plugin in pytester sessions, including under xdist, to check that it blocks unit-test process and socket I/O and enforces the unit-suite time budget
# relates: [clutch/testguard.py, test-gate.toml]
# owner: engine
# verified: d6229699
# hash: da534b37c51e88e0df415c130e8b33e5370380bdead1eabd4604dac0c28975b9

import os
import socket
import subprocess
from pathlib import Path

import pytest

pytest_plugins = ["pytester"]
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def inner_path(monkeypatch):
    monkeypatch.setenv("TESTGUARD_ELAPSED", "0")
    monkeypatch.setenv("PYTHONPATH", str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""))


def run(pytester, *args):
    return pytester.runpytest("-p", "clutch.testguard", "-o", "addopts=", *args)


def test_guarded_calls_and_asyncio(pytester):
    pytester.makepyfile("""
        import asyncio, os, socket, subprocess
        import pytest
        @pytest.mark.parametrize("action", [
            lambda: subprocess.run(["true"]),
            lambda: asyncio.run(asyncio.create_subprocess_exec("true")),
            lambda: os.system("true"),
            lambda: socket.socket().connect(("127.0.0.1", 9)),
            lambda: socket.getaddrinfo("localhost", 80),
            lambda: os.posix_spawn("/bin/true", ["true"], {}),
            lambda: os.posix_spawnp("true", ["true"], {}),
            lambda: socket.socket().connect_ex(("127.0.0.1", 9)),
            lambda: socket.socket().bind(("127.0.0.1", 0)),
        ])
        def test_blocked(action):
            action()
        def test_sleep():
            asyncio.run(asyncio.sleep(0))
    """)
    result = run(pytester)
    result.assert_outcomes(failed=9, passed=1)
    for i in range(9):
        section = result.stdout.str().split(f"test_blocked[<lambda>{i}]", 1)[1].splitlines()[1:]
        assert any("E       clutch.testguard.UnitIOBlocked:" in line for line in section[: next((j for j, line in enumerate(section) if line.startswith("________________")), len(section))])
    assert "seam (or a fake) instead" in result.stdout.str()
    assert "integration suite" not in result.stdout.str()


def test_setup_and_teardown(pytester):
    pytester.makepyfile("""
        import subprocess
        import pytest
        @pytest.fixture
        def before():
            subprocess.run(["true"])
            pytest.fail("setup process succeeded")
            yield
        @pytest.fixture
        def after():
            yield
            subprocess.run(["true"])
            pytest.fail("teardown process succeeded")
        def test_before(before): pass
        def test_after(after): pass
    """)
    result = run(pytester)
    result.assert_outcomes(passed=1, errors=2)
    output = result.stdout.str()
    assert "setup process succeeded" not in output
    assert "teardown process succeeded" not in output
    # pytest truncates the short-summary line to terminal width, so assert per ERROR section instead.
    sections = output.split("ERROR at ")[1:]
    assert len(sections) == 2 and all("clutch.testguard.UnitIOBlocked:" in section for section in sections)
    assert sections[0].startswith("setup of test_before") and sections[1].startswith("teardown of test_after")


def test_guards_are_phase_scoped(pytester):
    originals = (subprocess.Popen._execute_child, os.system, socket.socket.connect, socket.getaddrinfo)
    pytester.makeconftest("""
        import subprocess
        def pytest_configure(config):
            assert subprocess.run(["true"]).returncode == 0
    """)
    pytester.makepyfile("def test_pass(): pass")
    result = run(pytester)
    result.assert_outcomes(passed=1)
    assert (subprocess.Popen._execute_child, os.system, socket.socket.connect, socket.getaddrinfo) == originals


def fake_clock(pytester, elapsed, budget=None):
    if budget is not None:
        pytester.makefile(".toml", **{"test-gate": f"[coverage]\ndefault = 80\n[unit]\nbudget_seconds = {budget}\n"})
    os.environ["TESTGUARD_ELAPSED"] = str(elapsed)
    pytester.makeconftest("""
        import os
        import clutch.testguard
        values = iter([100, 100 + int(os.environ["TESTGUARD_ELAPSED"])])
        clutch.testguard.clock = lambda: next(values)
    """)


def test_budget_and_slowest(pytester):
    fake_clock(pytester, 6, 5)
    pytester.makepyfile("""
        import pytest
        def test_slowest(): pass
        def test_slower(): pass
        @pytest.mark.parametrize("n", range(10))
        def test_fast(n): pass
    """)
    pytester.makepyfile(
        slow_durations="""
        import pytest
        @pytest.hookimpl(wrapper=True)
        def pytest_runtest_makereport(item, call):
            report = yield
            if report.when == "call":
                report.duration = {"test_slowest": 2.0, "test_slower": 1.0}.get(item.name, 0.0)
            return report
    """
    )
    pytester.syspathinsert()
    result = run(pytester, "-p", "slow_durations")
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    lines = result.stdout.str().split("Unit suite took", 1)[1].split("Speed the listed", 1)[0]
    assert lines.index("test_slowest") < lines.index("test_slower")
    assert len([line for line in lines.splitlines() if "::test_" in line]) == 10
    fake_clock(pytester, 4, 5)
    assert run(pytester, "-p", "slow_durations").ret == pytest.ExitCode.OK


def test_xdist_budget(pytester):
    fake_clock(pytester, 6, 5)
    pytester.makepyfile("def test_worker(): pass")
    result = run(pytester, "-n", "2")
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert "::test_worker" in result.stdout.str().split("Unit suite took", 1)[1]


def test_default_and_invalid_budget(pytester):
    pytester.makepyfile("def test_pass(): pass")
    fake_clock(pytester, 59)
    assert run(pytester).ret == pytest.ExitCode.OK
    fake_clock(pytester, 61)
    assert run(pytester).ret == pytest.ExitCode.TESTS_FAILED
    fake_clock(pytester, 6, 0)
    result = run(pytester)
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert "unit.budget_seconds" in result.stderr.str()
