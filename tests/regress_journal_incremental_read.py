# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: regress journal incremental read
# relates: [clutch/journal.py]
# owner: clutch/journal.py
# verified: d7719818
# hash: 7896adcdd13d3669d6e9007bc9cb1d8e09b441e54643d417aff65aa2b3abc2e6
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from clutch import journal as module


def main():
    with tempfile.TemporaryDirectory() as directory:
        j = module.Journal(Path(directory), lambda: datetime(2026, 8, 4, tzinfo=UTC))
        for n in range(500):
            j.append("timer_armed", {"n": n})
        j.read()
        count = 0
        parse = module._parse_line

        def counted(path, lineno, raw):
            nonlocal count
            count += 1
            return parse(path, lineno, raw)

        module._parse_line = counted
        j.read()
        result = "pass" if count == 0 else "defect"
        print(json.dumps({"regression_result": result}))
        return 0 if result == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
