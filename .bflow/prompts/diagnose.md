# bflow-diagnose

Use this workflow when `bflow-replay` fails.

The workflow should:

1. Focus on the failed step and current page state.
2. Use `chrome-devtools` to inspect:
   - console errors
   - failed requests
   - missing DOM targets
   - blocking overlays or modals
3. Update `lifecycle.last_diagnosed_at` to the current ISO 8601 timestamp.
4. Do not rerun the full business flow unless the user asks.
5. Summarize the most likely root cause and the next recommended action.
