# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone regression probe that runs `clutch meta check` on an untracked path and reports a JSON pass, defect or error result depending on whether the path is refused with exit 2.
# relates: [clutch/__main__.py, tests/unit/test_meta_refresh.py]
# owner: engine
# verified: c8bbefc9
# hash: 599034ecef411ba40fe7a810b80e0f33af510d3306cf48c6a7530f4a52321359
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from clutch.__main__ import _run_meta
    from tests.unit.test_meta_refresh import MemoryFS, config
except ImportError:
    print(json.dumps({"regression_result": "error"}))
    sys.exit(2)

fs = MemoryFS({"docs/a.md": "body\n", "docs/new.md": "new\n"})
result = asyncio.run(_run_meta("check", config(), Path("/repo"), fs, ["docs/a.md"], "123456789", ("docs/new.md",)))
label, code = {0: ("defect", 1), 2: ("pass", 0)}.get(result, ("error", 2))
print(json.dumps({"regression_result": label}))
sys.exit(code)
