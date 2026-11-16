# Fact 4: repo facts for protus75/clutchwork

Captured 2026-11-16 UTC with read-only `gh api` GETs and plain curl. Nothing remote was mutated.

```
$ gh auth status          # token line omitted
github.com
  ✓ Logged in to github.com account protus75 (/home/djp/.config/gh/hosts.yml)
  - Git operations protocol: https
  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'

$ gh api repos/protus75/clutchwork --jq '{full_name, private, visibility, has_issues, archived, disabled, default_branch, permissions}'
{"archived":false,"default_branch":"main","disabled":false,"full_name":"protus75/clutchwork","has_issues":true,
 "permissions":{"admin":true,"maintain":true,"pull":true,"push":true,"triage":true},"private":true,"visibility":"private"}

$ gh api repos/protus75/clutchwork --jq '{has_issues, open_issues_count, has_discussions, html_url, license}'
{"has_issues":true,"open_issues_count":0,"has_discussions":false,"html_url":"https://github.com/protus75/clutchwork",
 "license":{"key":"other","name":"Other","spdx_id":"NOASSERTION",...}}

$ gh api repos/protus75/clutchwork/contents/.github
{"message":"Not Found",...,"status":"404"}gh: Not Found (HTTP 404)

$ gh api repos/protus75/clutchwork/community/profile     # trimmed
"issue_template":null,"pull_request_template":null,"license":{"key":"other",...}

$ gh api 'repos/protus75/clutchwork/labels?per_page=100' --jq '.[].name'
accessibility bug documentation duplicate enhancement good first issue help wanted invalid question wontfix

$ curl -sS -o /dev/null -w '%{http_code}\n' https://api.github.com/repos/protus75/clutchwork   # anonymous
404
$ curl -sS -o /dev/null -w '%{http_code} %{redirect_url}\n' https://github.com/protus75/clutchwork          # anonymous
404
$ curl -sS -o /dev/null -w '%{http_code} %{redirect_url}\n' https://github.com/protus75/clutchwork/issues   # anonymous
404
```

## Conclusion

- Issues are **enabled** (`has_issues: true`, 0 open). The repo has no `.github/` and no issue templates, so the blank form is served.
- The repo is **private** (`private: true`, `visibility: private`). An anonymous visitor gets a 404 for the repo, its issues and `issues/new`. Only signed-in accounts with repo access can open the prefilled form or submit an issue. A host operator who is not a collaborator on protus75/clutchwork gets a 404 page for every link the verb prints.
- This contradicts the plan's Privacy section ("The issue tracker is public"). Today the verb is usable only by the owner and invited collaborators, unless the repo is made public or the Repository URL points somewhere public. That is an owner decision, not something the hand test can settle.
- The license is proprietary (`LicenseRef-Proprietary`; GitHub reports "Other"/NOASSERTION), consistent with the repo being private.
