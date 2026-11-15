"""Reproducer: a second engine process overwrites the raw capture of a stem's earlier model call.

Usage: uv run python repro_provider_capture_overwrite.py <clutch checkout>
Prints one JSON line {"regression_result": "pass"|"defect"|"error"} on stdout; diagnostics on stderr.
"""

import asyncio
import json
import sys
import tempfile
import traceback
from pathlib import Path


def main() -> int:
    repo = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(repo))
    try:
        from tests.integration.test_providers import FakeExec, claude_ok, config, llm, req

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cfg = config(tmp)
            # Two engine processes, one after the other (a drain, then a later drain), each making one
            # model call for the same ticket. Each process builds its own ProviderLLM.
            first = llm(cfg, FakeExec((0, claude_ok("first run"), "")), tmp)
            asyncio.run(first.call(req("review")))
            second = llm(cfg, FakeExec((0, claude_ok("second run"), "")), tmp)
            asyncio.run(second.call(req("review")))

            root = cfg.state_dir / "spools" / "providers"
            captures = sorted(p.relative_to(root).as_posix() for p in root.rglob("events.jsonl"))
            texts = {c: (root / c).read_text() for c in captures}
            print(f"capture files after two runs: {captures}", file=sys.stderr)
            print(f"first run's transcript survived: {any('first run' in t for t in texts.values())}", file=sys.stderr)
            print(f"second run's transcript present: {any('second run' in t for t in texts.values())}", file=sys.stderr)
            ok = len(captures) == 2 and any("first run" in t for t in texts.values())
            if not ok:
                print("expected two capture files, one per call, with the first run's transcript intact", file=sys.stderr)
            verdict, code = ("pass", 0) if ok else ("defect", 1)
    except BaseException:
        traceback.print_exc(file=sys.stderr)
        verdict, code = "error", 2
    print(json.dumps({"regression_result": verdict}))
    return code


if __name__ == "__main__":
    sys.exit(main())
