"""Characterise the upper edge (414 / connection reset) of github.com URL length.

Usage: python3 -I probe_edge.py BASE_URL http2|http1.1 LEN [...]
One plain GET per length, no redirect follow, curl's minimal headers.
"""

import json
import subprocess
import sys
import time
from urllib.parse import quote

TITLE = "[critical:state-loss] probe title"


def main() -> None:
    base, proto = sys.argv[1], sys.argv[2]
    for raw in sys.argv[3:]:
        head = f"{base}?title={quote(TITLE, safe='')}&body="
        url = head + "a" * (int(raw) - len(head))
        argv = ["curl", "-sS", "--max-time", "30", f"--{proto}", "-o", "/dev/null",
                "-w", "%{http_code} %{http_version}", url]
        done = subprocess.run(argv, capture_output=True, text=True, check=False)
        print(json.dumps({"url_len": len(url), "proto": proto,
                          "result": done.stdout.strip(),
                          "curl_err": done.stderr.strip()[:120]}), flush=True)
        time.sleep(1.0)


if __name__ == "__main__":
    main()
