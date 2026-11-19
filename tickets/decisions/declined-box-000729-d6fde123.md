---
id: declined-box-000729-d6fde123
kind: declined
link: box-000729-d6fde123
reopen_after_days: 30
---
The note says `clutch release bump` changes only pyproject.toml, uv.lock and CHANGELOG.md and never changes the VS Code extension's version. It warns that the next kept extension package could reuse the version of the 0.3.0 package already in dist, and the Marketplace refuses a repeated version. It proposes that the release bump also set vscode-clutchwork/package.json's version.

The repeat the note predicts cannot happen today. The extension has its own version, and `./dev.py vscode` raises its patch number on every install (dev.py lines 85-91). package.json is now at 0.4.1, not the 0.3.0 the note reports. dist holds kept packages only up to vscode-clutchwork-0.3.0.vsix, and `./dev.py vscode-package` names the file from package.json's version, so the next kept package would be 0.4.1, a new version. Tying the extension version to the clutch release would change a policy, not fix a wrong behavior that is happening now. Reopen if a release keeps a .vsix whose version matches one already kept or uploaded, or if the Marketplace refuses an upload because the version repeats.

- clutch/release.py bumps only through `uv version --bump` and does not touch vscode-clutchwork/package.json.
- vscode-clutchwork/package.json line 5 has version 0.4.1; pyproject.toml has version 0.4.2.
- dev.py lines 85-91 raise package.json's patch version on every `./dev.py vscode` install.
- dev.py line 52 names the kept package dist/vscode-clutchwork-<package.json version>.vsix.
- The newest kept .vsix in dist is 0.3.0, so the current version 0.4.1 would not repeat it.

Message: box-000729-d6fde123
