# Fact 2: are `title`, `body`, `labels` honored?

Captured 2026-11-16 UTC by an agent with plain unauthenticated GETs. No login. The filled-in form itself is **not observable without signing in**, because `issues/new` always sends a signed-out visitor to login. What can be observed is below.

## 1. The login redirect carries all three parameters byte for byte

```
$ U='https://github.com/octocat/Hello-World/issues/new?title=%5Bcritical%3Astate-loss%5D%20probe&body=line%201%0A%60code%60%20%C3%A9&labels=bug'
$ curl -sS -o /dev/null -w '%{http_code}\n%{redirect_url}\n' "$U"
302
https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2Foctocat%2FHello-World%2Fissues%2Fnew%3Ftitle%3D%255Bcritical%253Astate-loss%255D%2520probe%26body%3Dline%25201%250A%2560code%2560%2520%25C3%25A9%26labels%3Dbug
$ python3 -I -c '<parse return_to, compare to $U, parse its query>'
return_to == request: True
{'title': ['[critical:state-loss] probe'], 'body': ['line 1\n`code` é'], 'labels': ['bug']}
```

The login page's hidden form field keeps the same URL: `<input type="hidden" name="return_to" id="return_to" value="https://github.com/octocat/Hello-World/issues/new?title=probe&amp;body=hello" ...>`. `raw/probe.py` checked the field against the request for every length up to 6,500 bytes, and it matched each time (fact 1, sweep 1). Brackets, a colon, a newline, backticks and non-ASCII text survive. For the private target, the 404 page's "Sign in" link carries the same full `return_to` (fact 1, sweep 4).

## 2. GitHub's documentation for the parameters

```
$ curl -sS -L -o creating-an-issue.html -w '%{http_code} %{url_effective}\n' \
    'https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue'
200 https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue
```

The section "Creating an issue from a URL query" (full text in `raw/docs_url_query_section.txt`) says:

- `title`: `issues/new?labels=bug&title=New+bug+report` "creates an issue with the label "bug" and title "New bug report.""
- `body`: `issues/new?title=New+bug+report&body=Describe+the+problem.` "creates an issue with the title "New bug report" and the comment "Describe the problem" in the issue body."
- `labels`: `issues/new?labels=help+wanted,bug`. But: "You must have the proper permissions for any action to use the equivalent query parameter. For example, you must have permission to add a label to an issue to use the labels query parameter." And: "If you create an invalid URL using query parameters, or if you don't have the proper permissions, the URL will return a 404 Not Found error page."
- `+` stands for a space in every example, so `urllib.parse.urlencode` output (space -> `+`) is a documented form.

## 3. No template chooser intercepts the link

```
$ gh api repos/protus75/clutchwork/contents/.github
{"message":"Not Found",...,"status":"404"}gh: Not Found (HTTP 404)
$ gh api repos/protus75/clutchwork/community/profile   # trimmed
"issue_template":null,"pull_request_template":null
```

The target repo has no `.github/` directory and no issue template, so `issues/new` serves the blank form, not the chooser. `octocat/Hello-World`, used for the probes, also has no `.github/`.

## Conclusion

- `title`, `body`: observed to pass through every redirect intact, and documented to prefill. That they appear in the rendered form was **not observed**, because that needs a signed-in browser. Under the owner's no-human-hand-test decision, the GitHub documentation plus the intact `return_to` is the evidence.
- `labels`: documented to need triage or label permission. Without it, GitHub documents a **404** for the whole link, not a silently ignored label. A host operator filing upstream is normally not a triager on the clutch repo, so the verb should **not** send `labels`. The `[critical:<class>]` title prefix already does the sorting job.
