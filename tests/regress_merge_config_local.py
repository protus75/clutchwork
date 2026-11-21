# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: verify local config survives squash merges
# relates: [clutch/merge.py]
# owner: clutch/merge.py
# verified: 365b3e38
# hash: bf3367d6ad63007d51e6f9c4082eeebe9c99efc02f1dc49472c0ee35244616e7
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from clutch.merge import dirty_overlap


async def main():
    git = SimpleNamespace(main_write=asyncio.Lock, status_porcelain=AsyncMock(return_value=" M config.yaml\0"), diff_names=AsyncMock(return_value=["config.yaml"]))
    return not await dirty_overlap(SimpleNamespace(git=git, repo="repo"), "work")


if __name__ == "__main__":
    passed = asyncio.run(main())
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    raise SystemExit(0 if passed else 1)
