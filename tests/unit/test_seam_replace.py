# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test seam replace
# relates: [clutch/seams.py]
# owner: clutch/seams.py
# verified: 9a610809
# hash: c8714a3598dbaa36fe3d8996c092474afa866a2d8dae80b2569f8bb501951ab6
import asyncio

import pytest

from clutch.seams import ExecutableNotFound, SubprocessExec


def test_replace_flushes_and_executes_in_order(monkeypatch, tmp_path):
    calls = []
    argv = ["engine", "argument"]
    env = {"PATH": "/custom/bin", "KEY": "value"}
    monkeypatch.setattr("clutch.seams.shutil.which", lambda binary, *, path: calls.append(("which", binary, path)) or "/custom/bin/engine")
    monkeypatch.setattr("clutch.seams.sys.stdout.flush", lambda: calls.append("stdout"))
    monkeypatch.setattr("clutch.seams.sys.stderr.flush", lambda: calls.append("stderr"))
    monkeypatch.setattr("clutch.seams.os.chdir", lambda cwd: calls.append(("chdir", cwd)))

    def execvpe(binary, args, environ):
        calls.append(("exec", binary, args, environ))
        raise RuntimeError("replaced")

    monkeypatch.setattr("clutch.seams.os.execvpe", execvpe)
    with pytest.raises(RuntimeError, match="replaced"):
        asyncio.run(SubprocessExec().replace(argv, cwd=tmp_path, env=env))
    assert calls == [("which", "engine", "/custom/bin"), "stdout", "stderr", ("chdir", tmp_path), ("exec", "engine", argv, env)]


def test_replace_missing_executable_does_not_change_process(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("clutch.seams.shutil.which", lambda binary, *, path: None)
    monkeypatch.setattr("clutch.seams.os.chdir", lambda cwd: calls.append("chdir"))
    monkeypatch.setattr("clutch.seams.os.execvpe", lambda *args: calls.append("exec"))
    with pytest.raises(ExecutableNotFound) as error:
        asyncio.run(SubprocessExec().replace(["missing"], cwd=tmp_path, env={"PATH": "/empty"}))
    assert error.value.binary == "missing"
    assert calls == []
