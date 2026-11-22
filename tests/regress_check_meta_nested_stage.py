# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone regression script checking that Driver.stage allows a nested meta stage inside an open check stage and restores the outer check stage afterward
# relates: [clutch/driver.py]
# owner: clutch/driver.py
# verified: ae8dbac1
# hash: 33f1d82d2daf04360c7210745f2c8216775a0f06b7fdf69ff4c71ce64a17f843
import json
from types import SimpleNamespace

from clutch.driver import Driver


def main():
    driver = Driver.__new__(Driver)
    driver._open_stage = None
    driver.log = SimpleNamespace(event=lambda *args, **kwargs: None)
    try:
        with driver.stage(stem="work", attempt=1, surface="check"):
            with driver.stage(stem="meta", attempt=1, surface="meta"):
                if driver._open_stage != ("meta", "meta"):
                    return False
            return driver._open_stage == ("work", "check")
    except ValueError:
        return False


if __name__ == "__main__":
    passed = main()
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    raise SystemExit(0 if passed else 1)
