# Case Files

Each file in this directory is a reusable browser-test definition.

## Required fields

- `name`
- `base_url`
- `goal`
- `lifecycle`
- `preconditions`
- `steps`
- `assertions`

## Optional fields

- `credentials`
- `artifacts`
- `notes`

## Recommended workflow

1. Create a draft from the template.
2. Fill the obvious business facts.
3. Keep `lifecycle.stage` at `draft` until the route is explored.
4. Use `bflow-explore` if the page path is not stable yet.
5. Move the case to `ready_for_replay` after exploration confirms the steps.
6. Keep the confirmed steps in the case file for future replays.
