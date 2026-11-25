"""Reproduce the engine text scan's binary logo failure."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: fixture
# purpose: Regression repro that runs the engine-text dev.py scan and reports, as JSON, whether it still fails on the binary clutch/assets/logo.png
# relates: [tests/integration/test_engine_text_verbs.py]
# owner: tests/integration/test_engine_text_verbs.py
# verified: d6f7e6b4
# hash: c713d7ec9446785e64f79cf79549861e35c1f5b4ae6bf4cd3f55171c582ddad3

import json
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    try:
        if not (root / "clutch" / "assets" / "logo.png").is_file():
            raise FileNotFoundError("clutch/assets/logo.png")
        from tests.integration.test_engine_text_verbs import test_no_engine_text_names_dev_py

        test_no_engine_text_names_dev_py()
    except AssertionError as error:
        if "clutch/assets/logo.png is not UTF-8" in str(error):
            result, code = "defect", 1
        else:
            result, code = "error", 2
    except Exception:
        result, code = "error", 2
    else:
        result, code = "pass", 0
    print(json.dumps({"regression_result": result}))
    return code


if __name__ == "__main__":
    sys.exit(main())
