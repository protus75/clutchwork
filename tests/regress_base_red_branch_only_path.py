"""Carried reproducer for verification commands naming branch-only paths."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Carried reproducer for verification commands naming branch-only paths.
# relates: []
# owner: engine
# verified: d7719818
# hash: 723d5f896ccca88d20f3b2eaea4fa6bf4cda6afa15bc9ee6cd32280484ae98d4

import contextlib
import json
import sys
import traceback


def main() -> int:
    try:
        import pytest

        with contextlib.redirect_stdout(sys.stderr):
            rc = pytest.main(["tests/integration/test_stages.py", "-k", "test_red_command_naming_a_branch_added_file_is_not_base_red", "-q", "-p", "no:cacheprovider"])
        if rc == 0:
            result, code = "pass", 0
        elif rc == 1:
            result, code = "defect", 1
        else:
            result, code = "error", 2
    except BaseException:
        traceback.print_exc(file=sys.stderr)
        result, code = "error", 2
    print(json.dumps({"regression_result": result}))
    return code


if __name__ == "__main__":
    sys.exit(main())
