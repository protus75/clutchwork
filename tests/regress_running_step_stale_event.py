# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone regression probe that reports pass or defect as JSON, depending on whether observe.current_step ignores a stage event from before the current run and returns the Starting step.
# relates: [clutch/observe.py]
# owner: clutch/observe.py
# verified: 778fd8bc
# hash: 391b0e6d28a46009e14325a190a02c7681a23279c86e500ef0237f01fea7c933
import inspect
import json
import sys

try:
    from clutch import observe
except ImportError:
    print(json.dumps({"regression_result": "error"}))
    sys.exit(2)


def main():
    t0 = "2026-11-22T13:31:16+00:00"
    since = "2026-11-22T15:17:16+00:00"
    log = [{"event": "stage_end", "stem": "alpha", "surface": "requisition_review", "ts": t0}]
    if len(inspect.signature(observe.current_step).parameters) < 3:
        result = observe.current_step(log, "alpha")
    else:
        result = observe.current_step(log, "alpha", since)
    passed = result == ("Starting", "", None)
    print(json.dumps({"regression_result": "pass" if passed else "defect"}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
