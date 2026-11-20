import asyncio
from pathlib import Path

from clutch.git import Git


def test_parse():
    class Exec:
        async def run(self, argv, **kwargs):
            assert "--first-parent" in argv and "--reverse" in argv
            return 0, "aaa\0a\n\x1e\nbbb\0b\n\x1e\nccc\0\x1e\nddd\0x\ny\n\x1e", ""

    assert asyncio.run(Git(Exec(), env={}, timeout=1, commit_lock=None).merged_tickets(Path("/repo"))) == [("aaa", "a"), ("bbb", "b")]
