# Fact 1: prefilled new-issue URL length limit

Captured 2026-11-16 ~03:00-03:10 UTC by an agent with plain unauthenticated GETs (curl 8.5.0, HTTP/2 unless noted). No login, no issue created.
Probe scripts and every raw JSONL row are in `raw/`. "URL length" below is the full encoded URL in bytes (`https://github.com/<owner>/<repo>/issues/new?title=...&body=...`); the body is padded with `a` unless noted.

## Target repo is private, so it was probed only for the edge behaviour

```
$ curl -sS -o /dev/null -D h1.txt -w 'code=%{http_code} redirect=%{redirect_url}\n' \
    'https://github.com/protus75/clutchwork/issues/new?title=probe&body=hello'
code=404 redirect=
```

An anonymous request gets a 404, not a login redirect (see fact 4: the repo is private). The length behaviour was therefore measured on a public repo with issues enabled and no issue templates, `octocat/Hello-World`, whose anonymous `issues/new` redirects to login. The limit is a github.com edge/front-end property: the private repo and a non-redirecting public page hit the same ceiling (tables below).

## Sweep 1: anonymous `issues/new`, curl's minimal headers

```
$ python3 -I raw/probe.py https://github.com/octocat/Hello-World/issues/new <LEN ...>
```

For each length the script sends one GET without following (status, `Location`, does `return_to` decode back to the exact request URL), then one GET with `-L` (final status, and whether the login form's hidden `return_to` field equals the request URL).

| URL len | status | Location len | return_to == request | follow status | form return_to == request |
|---:|---|---:|---|---|---|
| 200 | 302 | 267 | yes | 200 | yes |
| 2000 | 302 | 2067 | yes | 200 | yes |
| 4000 | 302 | 4067 | yes | 200 | yes |
| 6000 (x4) | 302 | 6067 | yes | 200 | yes |
| 6200 (x3) | 302 | 6267 | yes | 200 | yes |
| 6300 (x3) | 302 | 6367 | yes | 200 | yes |
| 6400 (x3) | 302 | 6467 | yes | 200 | yes |
| 6450 (x3) | 302 | 6517 | yes | 200 | yes |
| 6500 (x4) | 302 | 6567 | yes | 200 | yes |
| 6510 | 302 | 6577 | yes | **500** (login page) | - |
| 6530 | 302 | 6597 | yes | **500** | - |
| 6550, 6560, 6570, 6580 | **500** | - | - | 500 | - |
| 6590 | 302 (boundary noise) | 6657 | yes | 500 | - |
| 6600 ... 8000 | **500** | - | - | 500 | - |
| 8020 ... 8191 | connection reset (`curl: (56) Connection died`) | | | | |
| 8192, 8200 ... 64000 | **414** | | | | |
| 100000 | `curl: (55) Failed sending data to the peer` | | | | |

Every 500 is GitHub's "Internal server error · Whoops, something went wrong!" page (`raw/http500_headers.txt`; no `retry-after`, no rate-limit headers). Over HTTP/1.1 (`raw/probe_edge.py ... http1.1`): 6400 -> 302, 6600 ... 8000 -> 500, 8100 ... 8200 -> 502.

So, anonymous with curl's headers: the URL works up to 6,500 bytes, fails from about 6,510-6,590 bytes with a 500 (the boundary is noisy by ~50 bytes), and the 414 that GitHub's docs describe (`raw/docs_url_query_section.txt`: "If you create a URL that exceeds the server limit, the URL will return a 414 URI Too Long error page") appears only at 8,192 bytes. A prefilled link fails with a 500 page well before any 414. Nothing was silently truncated: below the ceiling `return_to` carried the full URL byte for byte; above it the request fails outright.

## Sweep 2: the same ceiling on other pages

```
$ python3 -I raw/probe.py https://github.com/octocat/Hello-World/issues <LEN ...>       # public page, no redirect
$ python3 -I raw/probe.py https://github.com/protus75/clutchwork/issues/new <LEN ...>   # the private target
```

| URL len | public `/issues` | private `clutchwork/issues/new` |
|---:|---|---|
| 1000 | - | 404 |
| 6000 | 200 | 404 |
| 6500 | 200 | 404 |
| 6550 | 200 | 500 |
| 6600 | 500 | 500 |
| 7000 | 500 | 500 |
| 8000 | 500 | 500 |
| 8192 | 414 | 414 |

## Sweep 3: the ceiling is on URL plus request headers, not the URL alone

A signed-in browser sends more header bytes (browser headers plus GitHub session cookies) than curl does. `raw/probe_headers.py` sends a browser-like header set (Chrome User-Agent, HTML Accept, Accept-Language: ~232 bytes of values) plus a dummy `Cookie: probe=ccc...` of a given size. The cookie is junk and carries no session.

```
$ python3 -I raw/probe_headers.py https://github.com/octocat/Hello-World/issues <URL_LEN:COOKIE_LEN ...>
```

| URL len | cookie value len | URL + cookie | status |
|---:|---:|---:|---|
| 200 | 0 ... 6000 (9 sizes) | <= 6200 | 200 (a large cookie alone is fine) |
| 200 | 6100 / 6200 | 6300 / 6400 | 200 / 200 |
| 200 | 6300 / 6400 / 6500 / 6600 | 6500 ... 6800 | 500 |
| 3000 | 3100 / 3200 / 3300 / 3400 | 6100 ... 6400 | 200 |
| 3000 | 3500 / 3600 | 6500 / 6600 | 500 |
| 6000 ... 6400 | 0 | 6000 ... 6400 | 200 |
| 6500 / 6600 | 0 | 6500 / 6600 | 500 |
| 6000 | 1000 | 7000 | 500 |
| 4000 | 3000 | 7000 | 500 |
| 2000 | 6000 | 8000 | 500 |

The 500 is set by the sum: URL + cookie must stay under about 6,450 bytes with this header set. With curl's smaller header set the URL alone reached 6,500. So GitHub's budget is roughly 6.5-6.7 KB for URL plus request header values combined. Every byte of a signed-in person's cookies comes out of the URL's share. A GitHub session cookie could not be measured without logging in.

## Sweep 4: the signed-out login detour costs more

A signed-out person who opens the link is sent to `https://github.com/login?return_to=<percent-encoded original URL>` (public repo: a 302; private repo: a "Sign in" link on the 404 page, `href="/login?return_to=https%3A%2F%2Fgithub.com%2Fprotus75%2Fclutchwork%2Fissues%2Fnew%3Ftitle%3Dprobe%26body%3Dhello"`). Each `%XX` in the original becomes `%25XX`, so the login URL is longer than the original. A body that is mostly escapes (`FILL=mixed`: spaces, backticks, `é`, newlines):

```
$ FILL=mixed python3 -I raw/probe.py https://github.com/octocat/Hello-World/issues/new <LEN ...>
```

| URL len | status | Location len | return_to == request | follow (login page) |
|---:|---|---:|---|---|
| 2000 | 302 | 3075 | yes | 200, form return_to intact |
| 3000 | 302 | 4621 | yes | 200, intact |
| 3500 | 302 | 5387 | yes | 200, intact |
| 4000 | 302 | 6153 | yes | 200, intact |
| 4500 | 302 | 6933 | yes | **500** |
| 5000 | 302 | 7699 | yes | **500** |
| 5200 ... 6000 | 302 | **24** (`https://github.com/login`) | **no: return_to dropped** | 200, but the prefill is lost |

This is the only truncation observed: once the redirect target would reach about 8 KB, GitHub drops `return_to` and sends a plain `/login`, so after signing in the person lands on their dashboard with no prefilled form. Below that, the login page itself 500s from a 6.1-6.9 KB login URL.

## Encoding ratio for a realistic body

```
$ python3 -I -c '... urllib.parse on docs/upstream-issue-plan.md lines 57-79 ...'   # raw/expansion.txt
sample chars 2265 utf8 bytes 2265
quote(safe="")   3237 1.43
quote_plus(safe="") 2547 1.12
base len 50
urlencode full url 2664
login detour url 3709 1.39
```

`urllib.parse.urlencode` (which uses `quote_plus`, so space becomes `+`) is about 1.12x for Markdown prose. Plain `quote` is about 1.43x. GitHub's own docs examples use `+` for spaces (`title=New+bug+report`), so `urlencode` is the cheaper encoding.

## Safe limit

Recommended refusal limit: **3,000 bytes for the whole printed link** (`len(url)` after encoding).

How the margin was chosen (estimates are labelled):

- Measured ceiling: about 6,500 bytes for URL + request header values combined (sweeps 1 and 3), with a ~50-byte noisy edge.
- Signed-in path (estimate): a browser's non-cookie headers are about 0.6 KB. A GitHub session Cookie header could not be observed without logging in; assume up to about 2.5 KB. That leaves about 3,400 bytes of URL.
- Signed-out path (measured ratio): the login detour is about 1.39x the link for prose and up to 1.53x for an all-escape body. It must fit about 5.7 KB after browser headers and anonymous cookies, which allows a link of about 3,700 bytes.
- 3,000 is about 46% of the measured ceiling. It clears both paths by about 400 bytes or more. With `urlencode` it still carries about 2,400 characters of Markdown body after the base URL, title and footer.

If a host operator still sees a GitHub 500 page with a link under 3,000 bytes, their cookie jar is larger than this estimate allows. The paved road is unchanged: shorten the body.
