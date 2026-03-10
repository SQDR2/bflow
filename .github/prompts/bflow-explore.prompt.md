---
mode: agent
description: Discover or refine the stable browser path for an existing case.
---

# bflow-explore

Discover or refine the stable browser path for an existing case.

User input: ${input:case:Enter the case name or path}
Example: /bflow-explore auth-login-smoke

Follow this workflow:

0. If `.bflow/` is missing in the current workspace, stop and tell the user to run `bflow init` in this project first.

1. Read `.bflow/README.md` and the requested case file under `.bflow/cases/`.
2. Use `agent-browser` to find a stable route for the business goal.
3. Write structured `steps` back into the case file.
4. Update `lifecycle.stage` to `ready_for_replay`, set `lifecycle.ready_for_replay=true`, and write the current ISO 8601 timestamp to `lifecycle.last_explored_at`.
5. Record unstable selectors, modals, redirects, or login-state risks in `notes`.
6. End by recommending `/bflow-replay`.

