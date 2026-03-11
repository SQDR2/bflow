---
agent: agent
description: Execute a saved browser-test case with chrome-devtools.
---

# bflow-replay

Execute an existing case with `chrome-devtools`.

User input: ${input:case:Enter the case name or path}
Example: /bflow-replay auth-login-smoke

Follow this workflow:

0. If `.bflow/` is missing in the current workspace, stop and tell the user to run `bflow init` in this project first.

1. Read `.bflow/README.md` and the requested case file under `.bflow/cases/`.
2. Use `chrome-devtools` to execute `steps` in order.
3. Do not replan the route unless the case explicitly says exploration is still pending.
4. If a page feature, label, route, or interaction target is unclear, pause browser actions and inspect the relevant workspace source code before continuing.
5. Keep that code lookup scoped to clarifying the current step or assertion. Do not turn it into broad re-exploration.
6. Check all `assertions`.
7. Write the current ISO 8601 timestamp to `lifecycle.last_replayed_at`.
8. Set `lifecycle.last_status` to `passed` or `failed` based on the outcome.
9. If the flow fails because the saved path is stale, set `lifecycle.stage` to `needs_diagnosis`.
10. Capture requested `artifacts` on failure.
11. Report executed steps, assertion results, any code evidence used for clarification, and failure evidence.

