"""Carried reproducer for scoped provider evidence."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for scoped provider evidence.
# relates: [clutch/effects.py, clutch/llmeffect.py, clutch/redact.py, tests/unit/test_evidence_envelope.py]
# owner: engine
# verified: d7719818
# hash: fb3e3330ac6901bd242c83ccf5391552f14b36da949c96b2bd06eed84ffe8ff2

import asyncio
import json
import sys
import tempfile
import traceback
from pathlib import Path


def main():
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import pytest

        from clutch.effects import Effects
        from clutch.llmeffect import llm_call, scoped_seq
        from clutch.redact import Redactor
        from tests.unit.test_evidence_envelope import ENV, Rig

        with tempfile.TemporaryDirectory() as directory, pytest.MonkeyPatch.context() as patch:
            rig = Rig(Path(directory), patch)
            key = "llm/ticket/sup-3/review/2/4"
            try:
                asyncio.run(
                    llm_call(Effects(rig.journal), rig.client, rig.request(), Redactor.from_config(rig.cfg, ENV), ticket="ticket", stem="ticket", run_seq=scoped_seq("sup", 3), attempt=2, call_seq=4)
                )
            except ValueError as exc:
                if "invalid literal for int()" not in str(exc):
                    raise
                print(json.dumps({"regression_result": "defect"}))
                return 1
            start = rig.store.read_record(key, "start")
            end = rig.store.read_record(key, "end")
            defect = not (start.id == key and start.run_seq == "sup-3" and end.exit.status == "ok" and any(argv[0] != "git" for argv, _ in rig.exec.calls))
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
