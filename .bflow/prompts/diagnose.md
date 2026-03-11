# bflow-diagnose

Use this workflow when `bflow-replay` fails.

The workflow should:

1. Focus on the failed step and current page state.
2. Use `chrome-devtools` to inspect:
   - console errors
   - failed requests
   - missing DOM targets
   - blocking overlays or modals
3. If the page behavior or failed control is still unclear, inspect the relevant workspace source code to understand the feature contract, conditional rendering, permissions, or request flow before concluding.
4. Keep that code lookup tightly scoped to the failure under diagnosis. Do not rerun the full exploration flow unless the user asks.
5. Update `lifecycle.last_diagnosed_at` to the current ISO 8601 timestamp.
6. Do not rerun the full business flow unless the user asks.
7. Summarize the most likely root cause, the code evidence used, and the next recommended action.
