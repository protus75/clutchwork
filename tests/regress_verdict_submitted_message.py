"""Carried reproducer for the live verdict submission message."""

import asyncio
import contextlib
import io
import json
import sys
import tempfile
import traceback
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from chupa import __main__ as entry
        from chupa import control, runner
        from chupa.lockfile import LockHeld

        request_id = "d8cdcd906b374c46bc7b46cc9f9978a3"
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            checkout = SimpleNamespace(repo=repo, journal=SimpleNamespace(read=lambda: []), config=SimpleNamespace(state_dir=repo / "state"), git=None, fs=None)
            output = io.StringIO()
            with (
                patch.object(runner, "verdict", AsyncMock(side_effect=LockHeld(repo / "chupa.lock", {"verb": "drain"}))),
                patch.object(runner, "ticket_pending", AsyncMock(return_value=False)),
                patch.object(control, "read_active", return_value=("life-1", None)),
                patch.object(control, "publish_request"),
                patch.object(entry, "uuid4", return_value=SimpleNamespace(hex=request_id)),
                contextlib.redirect_stdout(output),
            ):
                asyncio.run(entry._verdict(checkout, "sample", "confirm", None, True, False))
        lines = output.getvalue().splitlines()
        if not lines or " submitted: " not in lines[-1]:
            raise AssertionError(f"no submitted line: {lines!r}")
        if lines[-1] != f"confirm submitted: {request_id} -- `chupa status` shows the outcome":
            print(json.dumps({"regression_result": "defect"}))
            return 1
    except BaseException:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "pass"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
