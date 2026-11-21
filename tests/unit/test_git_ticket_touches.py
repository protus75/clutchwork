# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Parse ticket touches from a single git log call
# relates: [clutch/git.py]
# owner: clutch/git.py
# verified: 75d75946
# hash: 93dadafa7882f4a9482e778292a33ddcd6dbfae2b7ef679850b33aee8bde87b2
import asyncio
from pathlib import Path

from clutch.git import Git


def test_ticket_touches_parses_one_log_call():
    class Exec:
        calls = []

        async def run(self, argv, **kwargs):
            self.calls.append(argv)
            return 0, ("\x1eaaa\0a\n\0\0\nx.py\0y/z.md\0\x1ebbb\0b\n\0\0\nother.py\0\x1eccc\0\0\0\nunticketed.py\0\x1eddd\0x\ny\n\0\0\nduplicate.py\0"), ""

    exec_ = Exec()
    touches = asyncio.run(Git(exec_, env={}, timeout=1, commit_lock=None).ticket_touches(Path("/repo")))
    assert touches == [("a", "aaa", ["x.py", "y/z.md"]), ("b", "bbb", ["other.py"])]
    assert len(exec_.calls) == 1
    assert "--first-parent" in exec_.calls[0]
    assert "--reverse" in exec_.calls[0]
