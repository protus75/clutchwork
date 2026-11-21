# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test meta cli
# relates: [clutch/__main__.py, tests/unit/test_meta_refresh.py]
# owner: engine
# verified: bba3321b
# hash: 16cb24db7dafb8ee103858b84ab64d9c67000c7638bebb2d48a6664ace013837
import asyncio
from pathlib import Path

from clutch.__main__ import _run_meta
from tests.unit.test_meta_refresh import MemoryFS, config


def test_check_and_refusal(capsys):
    fs = MemoryFS({"docs/a.md": "body\n"})
    args = (config(), Path("/repo"), fs, ["docs/a.md"], "123456789")
    assert asyncio.run(_run_meta("check", *args)) == 1
    assert "missing" in capsys.readouterr().out
    assert asyncio.run(_run_meta("refresh", *args)) == 0
    assert asyncio.run(_run_meta("check", *args)) == 1
    assert "empty_purpose" in capsys.readouterr().out
    path = Path("/repo/docs/a.md")
    fs.files[path] = fs.files[path].replace(b"purpose:\n", b"purpose: useful\n")
    assert asyncio.run(_run_meta("check", *args)) == 0
    fs.files[path] += b"changed\n"
    assert asyncio.run(_run_meta("check", *args)) == 1
    assert "drifted" in capsys.readouterr().out
    fs.files[path] = b"<!-- clutch:meta\nbroken\n-->\n"
    assert asyncio.run(_run_meta("refresh", *args)) == 2
    assert " -- fix or remove" in capsys.readouterr().err
