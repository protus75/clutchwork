"""Reproduce snapshot tests running outside the checkout."""

import json
import subprocess
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "test_snapshot_verb_reads_config_state_dir",
    "test_observe_verbs_take_no_lock_and_write_nothing",
    "test_snapshot_watch_uses_configured_state",
)


def main() -> int:
    try:
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory) / "empty"
            cwd.mkdir()
            report = Path(directory) / "results.xml"
            test_file = ROOT / "tests/integration/test_watch.py"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-n",
                    "0",
                    "-p",
                    "no:cacheprovider",
                    "--rootdir",
                    str(ROOT),
                    "-c",
                    str(ROOT / "pyproject.toml"),
                    f"--junitxml={report}",
                    *(f"{test_file}::{name}" for name in NAMES),
                ],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            print(result.stdout, result.stderr, file=sys.stderr)
            cases = ET.parse(report).getroot().iter("testcase") if report.exists() else ()
            collected = [case.get("name") for case in cases]
            if sorted(collected) != sorted(NAMES):
                outcome, code = "error", 2
            elif result.returncode:
                outcome, code = "defect", 1
            else:
                outcome, code = "pass", 0
    except Exception:
        traceback.print_exc(file=sys.stderr)
        outcome, code = "error", 2
    print(json.dumps({"regression_result": outcome}))
    return code


if __name__ == "__main__":
    sys.exit(main())
