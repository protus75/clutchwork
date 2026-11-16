---
id: declined-box-000541-342d7edd
kind: declined
link: box-000541-342d7edd
reopen_after_days: 30
---
`clutch/release.py::release` runs `uv version --bump` and then commits pyproject.toml and uv.lock as two separate steps. If the process dies between them, the two files stay modified. Every later release then stops at the `uncommitted version files` check, and the driver's release-at-gate ship never goes through until someone restores the files. The note asks release to restore the files itself when no matching tag exists, or to make the bump and the commit one recoverable effect.

The crash window is real in the code: line 34 bumps, line 39 commits, and the guard at lines 19-21 refuses whenever the files are dirty. But this is a narrow kill window found by an audit, and no run has hit it. The failure is not silent either. The refusal names the files and gives a way out (`commit or restore pyproject.toml and uv.lock before release`), and an operator can follow it. The registry has declined earlier crash-window hardening with no observed incident, for example records 000016, 000110 and 000116. Reopen if a journaled driver ship or `clutch release` refusal shows a release stuck on version files left by an interrupted bump, or if an unattended release path with no operator becomes the only way releases happen.

- clutch/release.py:19-21 refuses when pyproject.toml or uv.lock is dirty, with a paved road to commit or restore them
- clutch/release.py:34 runs `uv version --bump`; clutch/release.py:39 commits only those files afterward; the steps are not one effect
- The message cites an audit of tickets/driver-loop/ticket.md, not an observed run or journal incident
- Precedent: declined crash-window notes 000016, 000110, 000116 without reproduced incidents

Message: box-000541-342d7edd
