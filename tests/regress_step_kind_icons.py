"""Carried reproducer for the Recent Steps icon vocabulary."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for the Recent Steps icon vocabulary.
# relates: [clutch/observe.py]
# owner: clutch/observe.py
# verified: d7719818
# hash: ea40a0fee974a0a630b3503b8d74f1b8f901edb3e4b7dcece583b29a6312e5b0

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    try:
        import clutch.observe as observe

        if not hasattr(observe, "STEP_KINDS"):
            outcome, code = "defect", 1
        else:
            kinds = observe.STEP_KINDS
            result = subprocess.run(
                ["node", str(Path(__file__).with_name("vscode_step_icons.js")), json.dumps(list(kinds))],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            icons = json.loads(result.stdout)
            if not isinstance(icons, dict) or set(icons) != set(kinds):
                raise ValueError("harness returned an invalid icon map")
            by_step = {}
            for kind, step in kinds.items():
                by_step.setdefault(step, set()).add(icons[kind])
            defect = any(not icon for icon in icons.values()) or any(len(ids) != 1 for ids in by_step.values()) or len({next(iter(ids)) for ids in by_step.values()}) != len(by_step)
            outcome, code = ("defect", 1) if defect else ("pass", 0)
    except (ImportError, OSError, subprocess.SubprocessError, ValueError) as error:
        print(error, file=sys.stderr)
        outcome, code = "error", 2
    print(json.dumps({"regression_result": outcome}))
    return code


if __name__ == "__main__":
    sys.exit(main())
