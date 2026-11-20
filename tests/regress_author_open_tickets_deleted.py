"""Carried reproducer for an indexed ticket deleted from the working tree."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for an indexed ticket deleted from the working tree.
# relates: [clutch/author.py]
# owner: clutch/author.py
# verified: d7719818
# hash: a4ab8d1286753900a0c9956f465d1d742cebf90dcbccc26df5a3881e7b0e9cb9

import asyncio
import json
import sys
import tempfile
import traceback
from pathlib import Path
from types import SimpleNamespace


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from clutch import author

        async def ls_files(repo):
            return ["tickets/gone/ticket.md", "tickets/live/ticket.md"]

        async def rev_parse(repo, ref):
            return "sha"

        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            live = repo / "tickets/live/ticket.md"
            live.parent.mkdir(parents=True)
            live.write_text("## Goal / Why\nlive goal\n")
            checkout = SimpleNamespace(repo=repo, git=SimpleNamespace(ls_files=ls_files, rev_parse=rev_parse), journal=SimpleNamespace(read=lambda: []))
            try:
                value = asyncio.run(author.list_open_tickets(checkout))
            except FileNotFoundError:
                print(json.dumps({"regression_result": "defect"}))
                return 1
        if value != "live: live goal":
            print(repr(value), file=sys.stderr)
            print(json.dumps({"regression_result": "error"}))
            return 2
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "pass"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
