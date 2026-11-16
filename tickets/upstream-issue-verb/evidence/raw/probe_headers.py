"""Does extra request-header weight (a dummy Cookie) move github.com's URL limit?

Usage: python3 -I probe_headers.py BASE_URL URL_LEN:COOKIE_LEN [...]
Sends a plain GET (no redirect follow) with a dummy `Cookie: probe=xxx...`
of COOKIE_LEN bytes of value and a browser-like header set, and prints one
JSON object per pair. The cookie is junk: it carries no session.
"""

import json
import subprocess
import sys
import time
from urllib.parse import quote

TITLE = "[critical:state-loss] probe title"
BROWSER_HEADERS = [
    "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language: en-US,en;q=0.9",
]


def main() -> None:
    base = sys.argv[1]
    for pair in sys.argv[2:]:
        url_len, cookie_len = (int(x) for x in pair.split(":"))
        head = f"{base}?title={quote(TITLE, safe='')}&body="
        url = head + "a" * (url_len - len(head))
        argv = ["curl", "-sS", "--max-time", "30", "-o", "/dev/null", "-w", "%{http_code}"]
        for h in BROWSER_HEADERS:
            argv += ["-H", h]
        if cookie_len:
            argv += ["-H", "Cookie: probe=" + "c" * cookie_len]
        argv.append(url)
        done = subprocess.run(argv, capture_output=True, text=True, check=False)
        print(json.dumps({
            "url_len": len(url),
            "cookie_value_len": cookie_len,
            "status": done.stdout.strip(),
            "curl_err": done.stderr.strip()[:120],
        }), flush=True)
        time.sleep(1.0)


if __name__ == "__main__":
    main()
