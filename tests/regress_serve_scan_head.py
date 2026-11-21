# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce needless intake invalidation by main commits without pending tickets.
# relates: [clutch/serve.py, tests/fakes.py]
# owner: engine
# verified: fc08bb14
# hash: 33497fc09626fef56381d84159f08912fbf70ecf5f85004654ace7ba41ba96c6
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

# Resolve the carried script's checkout, including when invoked on the merge base.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clutch.serve import Serve  # noqa: E402
from tests.fakes import FakeFileSystem, FakeJournal  # noqa: E402


async def reproduce():
    owner = Serve.__new__(Serve)
    owner.read, owner.stems = lambda stem: None, lambda: []
    git = SimpleNamespace(status_porcelain=AsyncMock(return_value=""), rev_parse=AsyncMock(return_value="a"))
    owner.checkout = SimpleNamespace(repo=Path("/unused"), fs=FakeFileSystem(), journal=FakeJournal(), git=git)
    before = await owner.intake_snapshot()
    git.rev_parse.return_value = "b"
    return before == await owner.intake_snapshot()


if __name__ == "__main__":
    passed = asyncio.run(reproduce())
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    sys.exit(0 if passed else 1)
