---
mode: agent
description: Create or update a browser-test case draft from a natural-language request.
---

# bflow-new

Create or update a case draft under `.bflow/cases/`.

User input: ${input:request:Describe the browser test you want to create}
Example: /bflow-new visit localhost:8080, sign in with admin / 123456, open the admin console, and verify the user list is visible

Follow this workflow:

0. If `.bflow/` is missing in the current workspace, stop and tell the user to run `bflow init` in this project first.

1. Read `.bflow/README.md` and `.bflow/cases/templates/test-flow.template.yaml`.
2. Infer a concise case name and a file path under `.bflow/cases/`.
3. Fill only the fields that are supported by the request.
4. If the request already includes obvious steps, add them to `steps`.
5. Set `lifecycle.stage` to `draft`, `lifecycle.ready_for_replay` to `false`, and `lifecycle.last_status` to `not_run`.
6. Do not invent missing selectors or paths.
7. Create or update the case file.
8. End by recommending `/bflow-explore` for the created case.

