# bflow

This directory contains the shared browser-test workflow assets for this project.

## What lives here

- `prompts/`
  - Workflow source prompts that describe how `bflow-new`, `bflow-explore`, `bflow-replay`, and `bflow-diagnose` should behave.
- `cases/`
  - Reusable browser-test case definitions for this project.
- `config.json`
  - The generated bflow configuration for this repo.

## Recommended workflow

1. Use `/bflow-new` to create a new case draft from a natural-language test description.
2. Use `/bflow-explore` to let `agent-browser` discover the stable path for that flow.
3. Write the confirmed steps back into the case file under `.bflow/cases/`.
4. Update the case lifecycle so the file reflects whether it is still a draft or ready for replay.
5. Use `/bflow-replay` to execute the stable steps with `chrome-devtools`.
6. Use `/bflow-diagnose` when a replay fails and you need console/network/DOM evidence.

## Where to add new test flows

Create new case files under `.bflow/cases/`. A good default is:

- `.bflow/cases/<domain>-<flow>-smoke.yaml`

Start from `.bflow/cases/templates/test-flow.template.yaml`.
