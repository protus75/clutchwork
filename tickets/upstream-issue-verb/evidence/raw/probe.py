"""Probe github.com prefilled new-issue URL length behaviour with plain GETs.

Usage: python3 -I probe.py BASE_URL LEN [LEN ...]
  BASE_URL  e.g. https://github.com/octocat/Hello-World/issues/new
  LEN       target total URL length in bytes (encoded), body padded to reach it
Env FILL=ascii|mixed picks the body filler (mixed percent-encodes to ~3x).
Prints one JSON object per length.
"""

import json
import os
import re
import subprocess
import sys
import time
from urllib.parse import parse_qs, quote, unquote, urlsplit

TITLE = "[critical:state-loss] probe title"
MIXED_UNIT = "line `x` é\n"  # spaces, backticks, non-ASCII, newline


def build(base: str, target: int, fill: str) -> str:
    head = f"{base}?title={quote(TITLE, safe='')}&body="
    room = target - len(head)
    if fill == "ascii":
        return head + "a" * max(room, 0)
    unit = quote(MIXED_UNIT, safe="")
    body = unit * (room // len(unit))
    return head + body + "a" * (room - len(body))


def curl(args: list[str]) -> tuple[str, str]:
    done = subprocess.run(
        ["curl", "-sS", "--max-time", "30", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return done.stdout, done.stderr


def probe(base: str, target: int, fill: str) -> dict:
    url = build(base, target, fill)
    row: dict = {"target": target, "url_len": len(url), "fill": fill}
    # No-follow request: status, Location, return_to fidelity.
    out, err = curl(
        ["-o", "/dev/null", "-D", "-", "-w", "\n@@%{http_code}", url]
    )
    headers, _, code = out.rpartition("\n@@")
    row["status"] = code.strip()
    loc = ""
    for line in headers.splitlines():
        if line.lower().startswith("location:"):
            loc = line.split(":", 1)[1].strip()
    row["location_len"] = len(loc)
    row["location_prefix"] = loc[:60]
    if loc:
        qs = parse_qs(urlsplit(loc).query)
        rt = qs.get("return_to", [""])[0]
        row["return_to_len"] = len(rt)
        row["return_to_equals_request"] = rt == url
        if rt:
            rq = parse_qs(urlsplit(rt).query)
            row["return_to_title_ok"] = rq.get("title", [""])[0] == TITLE
            want = parse_qs(urlsplit(url).query).get("body", [""])[0]
            row["return_to_body_ok"] = rq.get("body", [""])[0] == want
    if err:
        row["curl_err"] = err.strip()[:200]
    # Follow request: final status and whether the login form's hidden
    # return_to field still carries the whole original URL.
    out, err = curl(["-L", "-w", "\n@@%{http_code} %{num_redirects} %{url_effective}", url])
    page, _, tail = out.rpartition("\n@@")
    parts = tail.split(" ", 2)
    row["follow_status"] = parts[0]
    row["follow_redirects"] = parts[1] if len(parts) > 1 else ""
    row["follow_final_url_len"] = len(parts[2]) if len(parts) > 2 else 0
    row["follow_final_prefix"] = parts[2][:40] if len(parts) > 2 else ""
    m = re.search(r'name="return_to"[^>]*?value="([^"]*)"', page)
    if m:
        field = m.group(1)
        # HTML attribute escaping: &amp; for &
        field = field.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
        row["form_return_to_len"] = len(field)
        row["form_return_to_equals_request"] = field == url or unquote(field) == unquote(url)
    else:
        row["form_return_to_len"] = None
    if err:
        row["follow_curl_err"] = err.strip()[:200]
    return row


def main() -> None:
    base = sys.argv[1]
    fill = os.environ.get("FILL", "ascii")
    for raw in sys.argv[2:]:
        print(json.dumps(probe(base, int(raw), fill)), flush=True)
        time.sleep(1.0)


if __name__ == "__main__":
    main()
