---
id: declined-box-000446-77e30de5
kind: declined
link: box-000446-77e30de5
reopen_after_days: 30
---
Proposes an optional `clutch[node]` Python extra that ships a Node.js and pnpm wheel (such as nodejs-wheel-binaries), so `clutch install` can install provider CLIs on a host that has no Node.js. It is meant as a follow-up to the open ticket provider-cli-install.

No current behavior gap is shown. `clutch install` does not exist yet: provider-cli-install is still open and unmerged, so no run has failed because a host lacks Node.js. The idea is speculative hardening for a verb that has not been built. It is also not a duplicate. provider-cli-install covers project-local pnpm dev-dependency installs and a `node_modules/.bin` PATH prefix, and it never mentions bundling Node.js or pnpm. Reopen once provider-cli-install has merged and a real host without Node.js or pnpm has `clutch install` refuse or fail, with the command and output recorded.

- tickets/provider-cli-install/ticket.md is in open_tickets, not merged, and defines the `clutch install` verb that this suggestion extends.
- tickets/provider-cli-install/ticket.md:48 says the CLIs are npm packages that a Python extra cannot carry, and it uses pnpm `add -D` into `node_modules/.bin`. Nothing in the ticket bundles Node.js or pnpm.
- The message has origin `session` and gives no stage, outcome, or report showing a host without Node.js failing.

Message: box-000446-77e30de5
