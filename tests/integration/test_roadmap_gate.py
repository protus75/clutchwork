# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that `clutch roadmap gate` runs real gate commands and journals the results, and that the repository roadmap gate blocks have the expected shape
# relates: [clutch/__main__.py, clutch/journal.py, clutch/roadmap.py, tests/integration/test_cli.py]
# owner: clutch/roadmap.py
# verified: 628fcc0e
# hash: dd0d7a7385a23fbf0dd734f29f6f391d6e33be0bbd08f5e5f27c0ecc4daee8c0
import shlex
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

import clutch.__main__ as cli
from clutch import roadmap
from clutch.journal import EventType, Journal
from tests.cli_helpers import CONFIG, ENV

pytestmark = pytest.mark.disk_io_skip


def test_roadmap_gate_runs_real_commands(tmp_path, capsys):
    (tmp_path / "config.yaml").write_text(CONFIG)
    path = tmp_path / roadmap.ROADMAP
    path.parent.mkdir()
    first = shlex.join([sys.executable, "-c", "print('hi')"])
    second = shlex.join([sys.executable, "-c", "import sys; print('boom', file=sys.stderr); sys.exit(4)"])
    path.write_text(f"### 1.0.0\n```gate\n{first}\n{second}\n```\n")
    # Real nonzero process status and stderr must reach the CLI and persistent journal.
    assert cli.main(["roadmap", "gate", "1.0.0"], cwd=tmp_path, env=ENV) == 1
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == (f"gate 1.0.0: ok: {first}\ngate 1.0.0: failed (exit 4): {second} -- boom\ngate 1.0.0: failed\n", "")
    journal = Journal(tmp_path / ".clutch/state", lambda: datetime.now(UTC))
    assert [(e.type, e.body) for e in journal.read()] == [(EventType.SIGNAL, {"signal": "roadmap_gate", "release": "1.0.0", "passed": False, "failed": second})]
    path.write_text(f"### 1.0.0\n```gate\n{first}\n```\n")
    assert cli.main(["roadmap", "gate", "1.0.0"], cwd=tmp_path, env=ENV) == 0
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == (f"gate 1.0.0: ok: {first}\ngate 1.0.0: passed\n", "")
    # Check both persisted bodies: replacing the previous event cannot pass this assertion.
    assert [(e.type, e.body) for e in journal.read()] == [
        (EventType.SIGNAL, {"signal": "roadmap_gate", "release": "1.0.0", "passed": False, "failed": second}),
        (EventType.SIGNAL, {"signal": "roadmap_gate", "release": "1.0.0", "passed": True, "failed": None}),
    ]


def test_real_roadmap_gate_blocks():
    text = (Path(__file__).resolve().parents[2] / roadmap.ROADMAP).read_text()
    rows = roadmap.parse(text)
    blocks = roadmap.gates(text)
    releases = {roadmap.release_name(row.release) for row in rows}
    # Missing blocks and extra blocks must both be detected.
    assert set(blocks) == releases
    first = roadmap.release_name(rows[0].release)
    # No hard-coded version, swapped order, or omitted evidence/count condition passes.
    assert blocks[first] == (
        ("uv", "run", "clutch", "roadmap", "merged", "--release", first, "--priority", "P0", "P1"),
        ("uv", "run", "clutch", "roadmap", "merged", "docs-truth-sweep", "evidence-envelope"),
        ("uv", "run", "clutch", "roadmap", "merged", "--since", f"v{first}", "--at-least", "3", "--source", "box:roadmap_row", "--unattended"),
        ("./dev.py", "test"),
        ("uv", "run", "clutch", "roadmap", "accept", first),
    )
    for release in releases - {first}:
        commands = blocks[release]
        assert commands[0] == ("uv", "run", "clutch", "roadmap", "merged", "--release", release)
        assert commands[-2:] == (("./dev.py", "test"), ("uv", "run", "clutch", "roadmap", "accept", release))
        assert all(command[:3] == ("uv", "run", "clutch") for command in commands[1:-2])
        if release not in ("0.4.0", "0.5.0", "0.6.0", "0.7.0"):
            assert len(commands) == 3
    for release, commands in blocks.items():
        assert commands[-1] == ("uv", "run", "clutch", "roadmap", "accept", release)
        assert commands[-2] == ("./dev.py", "test")
        assert commands.count(("./dev.py", "test")) == 1
        for command in commands:
            if command[:3] == ("uv", "run", "clutch"):
                cli._parser().parse_args(command[3:])
