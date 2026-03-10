---
agent: agent
description: Discover or refine the stable browser path for an existing case.
---

# bflow-explore

Discover or refine the stable browser path for an existing case.

User input: ${input:case:Enter the case name or path}
Example: /bflow-explore auth-login-smoke

Follow this workflow:

0. If `.bflow/` is missing in the current workspace, stop and tell the user to run `bflow init` in this project first.

1. Read `.bflow/README.md` and the requested case file under `.bflow/cases/`.
2. Inspect the current agent tool configuration before doing any browser actions.
3. If `agent-browser` is unavailable, stop immediately and tell the user that the current agent is not configured with `agent-browser`.
4. In that stop message, ask the user to install or connect `agent-browser` for the current agent before rerunning `/bflow-explore`.
5. Do not silently fall back to `chrome-devtools`, and do not start deterministic replay-style execution in this workflow.
6. Use `agent-browser` to find a stable route for the business goal.
7. Write structured `steps` back into the case file.
8. Update `lifecycle.stage` to `ready_for_replay`, set `lifecycle.ready_for_replay=true`, and write the current ISO 8601 timestamp to `lifecycle.last_explored_at`.
9. Record unstable selectors, modals, redirects, or login-state risks in `notes`.
10. End by recommending `/bflow-replay`.

