"""Reproduce implicit queue-order edges in the Tickets graph."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Reproduce implicit queue-order edges in the Tickets graph.
# relates: [clutch/graph.py]
# owner: clutch/graph.py
# verified: d7719818
# hash: 4b81e713c37692977a9fc8a5e961f5850b4732b2fbe91c1617d99414b8952774

import json
import sys
import traceback
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from clutch.graph import layout

        rows = [
            {"stem": "check-test-timing", "section": "queued", "depends": []},
            {"stem": "results-schema-2-reader", "section": "queued", "depends": []},
            {"stem": "vscode-verdict-menu", "section": "queued", "depends": ["review-unmerged-provisional"]},
            {"stem": "review-unmerged-provisional", "section": "queued", "depends": []},
            {"stem": "finished", "section": "merged", "depends": []},
        ]
        defect = any(parent not in row["depends"] for row, graph in zip(rows, layout(rows)) if row["section"] != "merged" for parent in graph["parents"])
    except Exception:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"regression_result": "error"}))
        return 2
    print(json.dumps({"regression_result": "defect" if defect else "pass"}))
    return 1 if defect else 0


if __name__ == "__main__":
    sys.exit(main())
