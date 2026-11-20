# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test git merged tickets parse
# relates: [clutch/git.py]
# owner: clutch/git.py
# verified: 0a308920
# hash: 9b04027917851f8e89b8f06cdd9642137546fe839af7e920f9fc1d8d401fcd48
import asyncio
from pathlib import Path

from clutch.git import Git


def test_parse():
    class Exec:
        async def run(self, argv, **kwargs):
            assert "--first-parent" in argv and "--reverse" in argv
            return 0, "aaa\0a\n\x1e\nbbb\0b\n\x1e\nccc\0\x1e\nddd\0x\ny\n\x1e", ""

    assert asyncio.run(Git(Exec(), env={}, timeout=1, commit_lock=None).merged_tickets(Path("/repo"))) == [("aaa", "a"), ("bbb", "b")]
