# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test handoff replace
# relates: []
# owner: engine
# verified: 148a8874
# hash: e93cf07becbe54b1039f4702f5a6cd4b7a9993c5490bb059b7a824f2b8a24899
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_replacement_preserves_pid_exit_code_and_buffered_output(tmp_path):
    script = """import asyncio, os, sys
from pathlib import Path
from clutch.seams import SubprocessExec
print('buffered before replace')
asyncio.run(SubprocessExec().replace([sys.executable, '-c', 'import os, sys; print(os.getpid()); sys.exit(7)'], cwd=Path.cwd(), env=os.environ))
"""
    child = subprocess.Popen([sys.executable, "-c", script], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = child.communicate(timeout=20)
    assert child.returncode == 7
    assert out.splitlines() == ["buffered before replace", str(child.pid)]
    assert err == ""


def test_handoffs_do_not_spawn_unbounded_children():
    for name in ("clutch/drain.py", "clutch/serve.py"):
        assert "timeout=None" not in (ROOT / name).read_text()
    assert "self-upgrade handoff" not in (ROOT / "clutch/seams.py").read_text()
    assert "releases the lock, and spawns the new serve" not in (ROOT / "docs/how-clutch-works.md").read_text()
