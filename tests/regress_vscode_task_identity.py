"""Carried reproducer for VS Code task identity across clutch actions."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for VS Code task identity across clutch actions.
# relates: []
# owner: engine
# verified: d7719818
# hash: d669930c6e1bf00c6d238ec90497d3c9d7e86796146bfb97d22106d94f04dd33

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    try:
        result = subprocess.run(
            ["node", str(Path(__file__).with_name("vscode_task_identity.js"))],
            capture_output=True,
            text=True,
            check=True,
        )
        definitions = json.loads(result.stdout)
        if not isinstance(definitions, list) or len(definitions) < 3:
            raise ValueError("fewer than three task definitions")
        review, lint, repeated = definitions[:3]
        if review == lint:
            outcome, code = "defect", 1
        elif review == repeated:
            outcome, code = "pass", 0
        else:
            raise ValueError("identical actions have different task definitions")
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        print(error, file=sys.stderr)
        outcome, code = "error", 2
    print(json.dumps({"regression_result": outcome}))
    return code


if __name__ == "__main__":
    sys.exit(main())
