---
mode: agent
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
4. Check all `assertions`.
5. Write the current ISO 8601 timestamp to `lifecycle.last_replayed_at`.
6. Set `lifecycle.last_status` to `passed` or `failed` based on the outcome.
7. If the flow fails because the saved path is stale, set `lifecycle.stage` to `needs_diagnosis`.
8. Capture requested `artifacts` on failure.
9. Report executed steps, assertion results, and failure evidence.

