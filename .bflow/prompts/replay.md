# bflow-replay

Use this workflow to execute a stable case with `chrome-devtools`.

The workflow should:

1. Read the target case from `.bflow/cases/`.
2. Execute the `steps` in order without replanning the flow.
3. Check the listed `assertions`.
4. Update `lifecycle.last_replayed_at` to the current ISO 8601 timestamp.
5. If the replay passes, set `lifecycle.last_status` to `passed`; otherwise set it to `failed`.
6. Capture requested `artifacts` on failure.
7. Summarize:
   - executed steps
   - assertion results
   - failed step
   - console summary
   - network summary
