# bflow-explore

Use this workflow when a case exists but the exact page path is missing or unstable.

The workflow should:

1. Read the target case file from `.bflow/cases/`.
2. Use `agent-browser` to find a stable route for the business goal.
3. Output structured steps with:
   - `action`
   - `target`
   - `value` or `value_from`
   - `expected`
   - `risk`
4. Update the case file with the discovered `steps`.
5. Set `lifecycle.stage` to `ready_for_replay`, `lifecycle.ready_for_replay` to `true`, and `lifecycle.last_explored_at` to the current ISO 8601 timestamp.
6. Explain any unstable selectors or modal risks.
7. End by recommending `bflow-replay`.
