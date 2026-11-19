"""One-time end-to-end snapshot latency and completeness check."""

import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from tests.snapshot_scale_fixture import build


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fixture = build(root)
        if fixture["events"] < 37763 or fixture["tickets"] < 694 or fixture["box"] < 791:
            print(json.dumps({"error": "fixture counts below thresholds"}))
            return 2
        env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
        times = []
        for i in range(4):
            start = time.perf_counter()
            proc = subprocess.run([sys.executable, "-m", "clutch", "view", "snapshot"], cwd=root, env=env, capture_output=True, text=True)
            elapsed = time.perf_counter() - start
            if proc.returncode:
                print(json.dumps({"error": proc.stderr}))
                return 2
            data = json.loads(proc.stdout)
            for key, expected, actual in (("stems", fixture["stems"], [r["stem"] for r in data["rows"]]), ("ids", fixture["ids"], [r["id"] for r in data["box"]])):
                if sorted(expected) != sorted(actual):
                    print(json.dumps({"error": f"{key}: missing {sorted(set(expected) - set(actual))}; extra {sorted(set(actual) - set(expected))}; counts {len(expected)} vs {len(actual)}"}))
                    return 2
            times.append(elapsed)
        median = statistics.median(times[1:])
        print(json.dumps(dict(cold_s=times[0], timings_s=times[1:], median_s=median, events=fixture["events"], tickets=fixture["tickets"], box=fixture["box"])))
        return 0 if median < 2 else 1


if __name__ == "__main__":
    sys.exit(main())
