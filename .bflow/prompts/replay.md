# bflow-replay

Use this workflow to execute a stable case with `chrome-devtools`.

The workflow should:

1. Read the target case from `.bflow/cases/`.
2. Execute the `steps` in order without replanning the flow.
3. If a page feature or action target is ambiguous during execution, pause browser actions and inspect the relevant workspace code to understand the current UI behavior before continuing.
4. Use that code lookup only to clarify the current step or assertion. Do not freely re-explore the route or invent behavior that is not supported by the case or the code.
5. Check the listed `assertions`.
6. Update `lifecycle.last_replayed_at` to the current ISO 8601 timestamp.
7. If the replay passes, set `lifecycle.last_status` to `passed`; otherwise set it to `failed`.
8. Capture requested `artifacts` on failure.
9. Summarize:
   - executed steps
   - assertion results
   - failed step
    - code evidence used for clarification
   - console summary
   - network summary
