# bflow-explore

Use this workflow when a case exists but the exact page path is missing or unstable.

The workflow should:

1. Read `.bflow/README.md`, `.bflow/config.json`, `.bflow/agent-browser-setup.md`, and the target case file from `.bflow/cases/`.
2. Check the current agent tool configuration before any browser action.
3. Verify that the current running agent is declared in `.bflow/config.json` and that this agent has `agent-browser` available.
4. If that verification fails, stop immediately. Do not use `chrome-devtools`, `chrome-devtools-mcp`, or any other browser automation tool to continue exploration.
5. In that stop message, tailor the reply to the current agent configuration: name the current agent, list the configured agents from `.bflow/config.json`, and give the matching `agent-browser` setup command from `.bflow/agent-browser-setup.md` when available.
6. If the current agent is not listed in `.bflow/config.json`, tell the user to rerun `bflow init --agents ...` for that agent or switch to one of the configured agents before rerunning `bflow-explore`.
7. Only after verification passes, use `agent-browser` to find a stable route for the business goal.
8. Output structured steps with:
   - `action`
   - `target`
   - `value` or `value_from`
   - `expected`
   - `risk`
9. Update the case file with the discovered `steps`.
10. Set `lifecycle.stage` to `ready_for_replay`, `lifecycle.ready_for_replay` to `true`, and `lifecycle.last_explored_at` to the current ISO 8601 timestamp.
11. Explain any unstable selectors or modal risks.
12. End by recommending `bflow-replay`.
