"""Carried reproducer for a provider install with a broken binary."""

import contextlib
import io
import json
import sys
import traceback
from pathlib import Path
from unittest.mock import patch


def main() -> int:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from clutch import __main__ as cli

        class FakeExec:
            async def run(self, argv, **kwargs):
                if argv[0] == "pnpm":
                    return 0, "", ""
                return 1, "", "Error: claude native binary not installed.\n"

        with patch.object(cli, "SubprocessExec", FakeExec), contextlib.redirect_stdout(io.StringIO()):
            rc = cli.main(["provider", "install", "claude"], cwd=Path("/repo"), env={"PATH": "/bin"})
        if rc not in (0, 2):
            raise ValueError(f"unexpected exit code: {rc}")
        defect = rc == 0
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
