# Router Prompt

Use this prompt when you need a single high-level rule set for the `bflow` workflow.

```text
You have two browser tools:
- agent_browser: use for exploration and path finding
- chrome_devtools: use for deterministic execution, assertions, screenshots, and diagnostics

Routing rules:
1. If the page path is unknown or unstable, start with `bflow-explore`.
2. If the steps are already known, use `bflow-replay`.
3. If the user only has a natural-language request and no case file yet, use `bflow-new`.
4. If a replay fails, use `bflow-diagnose`.
```
