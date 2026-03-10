# bflow-explore

Use this workflow when a case exists but the exact page path is missing or unstable.

The workflow should:

1. Read the target case file from `.bflow/cases/`.
2. Check the current agent tool configuration first.
3. If `agent-browser` is not available in the current agent, stop immediately and tell the user that this agent is not configured with `agent-browser`.
4. In that stop message, ask the user to install or connect `agent-browser` for the current agent before rerunning `bflow-explore`.
5. Do not silently fall back to `chrome-devtools` during exploration.
6. Use `agent-browser` to find a stable route for the business goal.
7. Output structured steps with:
   - `action`
   - `target`
   - `value` or `value_from`
   - `expected`
   - `risk`
8. Update the case file with the discovered `steps`.
9. Set `lifecycle.stage` to `ready_for_replay`, `lifecycle.ready_for_replay` to `true`, and `lifecycle.last_explored_at` to the current ISO 8601 timestamp.
10. Explain any unstable selectors or modal risks.
11. End by recommending `bflow-replay`.
