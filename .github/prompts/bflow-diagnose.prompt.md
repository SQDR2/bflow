---
agent: agent
description: Diagnose a failed browser-test replay using console, network, and DOM evidence.
---

# bflow-diagnose

Diagnose a failed replay with evidence-first analysis.

User input: ${input:case:Enter the case name or path}
Example: /bflow-diagnose auth-login-smoke

Follow this workflow:

0. If `.bflow/` is missing in the current workspace, stop and tell the user to run `bflow init` in this project first.

1. Read `.bflow/README.md` and the requested case file under `.bflow/cases/`.
2. Focus on the failed step and current page state.
3. Use `chrome-devtools` to inspect console errors, failed requests, missing DOM targets, and blocking overlays.
4. If the page behavior or failed control is still unclear, inspect the relevant workspace source code to understand the feature contract, conditional rendering, permissions, or request flow.
5. Keep that code lookup scoped to the current failure instead of broad re-exploration.
6. Write the current ISO 8601 timestamp to `lifecycle.last_diagnosed_at` and keep `lifecycle.stage=needs_diagnosis` until the route is fixed.
7. Do not rerun the entire business flow unless the user asks.
8. Report the most likely root cause, the code evidence used, and the next action.

