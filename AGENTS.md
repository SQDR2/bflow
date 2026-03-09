<!-- bflow:begin -->
## bflow Workflow

This repository uses `bflow` for browser-test workflows.

Important files:

- `.bflow/README.md`
- `.bflow/prompts/`
- `.bflow/cases/`

If the user types one of these aliases, treat it as a workflow command:

- `/bflow-new <request>`: create or update a case draft under `.bflow/cases/`
- `/bflow-explore <case-name-or-path>`: use `agent-browser` to discover or refine steps
- `/bflow-replay <case-name-or-path>`: use `chrome-devtools` to execute the case
- `/bflow-diagnose <case-name-or-path>`: inspect a replay failure

Workflow rules:

1. `/bflow-new` creates or updates the case file, keeps `lifecycle.stage=draft`, and ends by recommending `/bflow-explore`.
2. `/bflow-explore` is for path discovery, not final regression execution, and should promote the case to `ready_for_replay` when the steps are stable.
3. `/bflow-replay` runs the saved steps without replanning the business flow and updates replay timestamps/status.
4. `/bflow-diagnose` focuses on evidence and root cause, not broad re-exploration, and updates diagnosis metadata.
<!-- bflow:end -->
