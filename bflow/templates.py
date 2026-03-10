from __future__ import annotations

import json
import sys
from pathlib import Path


WORKFLOW_NAMES = ("new", "explore", "replay", "diagnose")
SUPPORTED_AGENTS = ("claude", "opencode", "copilot", "codex")

WORKFLOW_METADATA = {
    "new": {
        "description": "Create or update a browser-test case draft from a natural-language request.",
        "argument_hint": "[natural-language test request]",
        "example": "visit localhost:8080, sign in with admin / 123456, open the admin console, and verify the user list is visible",
    },
    "explore": {
        "description": "Discover or refine the stable browser path for an existing case.",
        "argument_hint": "[case name or path]",
        "example": "auth-login-smoke",
    },
    "replay": {
        "description": "Execute a saved browser-test case with chrome-devtools.",
        "argument_hint": "[case name or path]",
        "example": "auth-login-smoke",
    },
    "diagnose": {
        "description": "Diagnose a failed browser-test replay using console, network, and DOM evidence.",
        "argument_hint": "[case name or path]",
        "example": "auth-login-smoke",
    },
}


def shared_project_files(prefix: str, agents: list[str], scope: str) -> dict[str, str]:
    config = {
        "version": "0.1.0",
        "prefix": prefix,
        "scope": scope,
        "agents": agents,
        "commands": [f"{prefix}-{name}" for name in WORKFLOW_NAMES],
    }
    return {
        ".bflow/config.json": json.dumps(config, indent=2) + "\n",
        ".bflow/README.md": shared_readme(prefix),
        ".bflow/prompts/router.md": router_prompt(prefix),
        ".bflow/prompts/new.md": new_prompt(prefix),
        ".bflow/prompts/explore.md": explore_prompt(prefix),
        ".bflow/prompts/replay.md": replay_prompt(prefix),
        ".bflow/prompts/diagnose.md": diagnose_prompt(prefix),
        ".bflow/cases/README.md": cases_readme(),
        ".bflow/cases/templates/test-flow.template.yaml": case_template(),
        ".bflow/cases/examples/login-admin-smoke.yaml": example_case(),
    }


def shared_readme(prefix: str) -> str:
    return f"""# bflow

This directory contains the shared browser-test workflow assets for this project.

## What lives here

- `prompts/`
  - Workflow source prompts that describe how `{prefix}-new`, `{prefix}-explore`, `{prefix}-replay`, and `{prefix}-diagnose` should behave.
- `cases/`
  - Reusable browser-test case definitions for this project.
- `config.json`
  - The generated bflow configuration for this repo.

## Prerequisites

Before you use replay or diagnose workflows in any agent, install `chrome-devtools-mcp` in that agent first:

- https://github.com/ChromeDevTools/chrome-devtools-mcp

If you plan to use exploration workflows, install your `agent-browser` integration as well.

## Recommended workflow

1. Use `/{prefix}-new` to create a new case draft from a natural-language test description.
2. Use `/{prefix}-explore` to let `agent-browser` discover the stable path for that flow.
3. Write the confirmed steps back into the case file under `.bflow/cases/`.
4. Update the case lifecycle so the file reflects whether it is still a draft or ready for replay.
5. Use `/{prefix}-replay` to execute the stable steps with `chrome-devtools`.
6. Use `/{prefix}-diagnose` when a replay fails and you need console/network/DOM evidence.

## Where to add new test flows

Create new case files under `.bflow/cases/`. A good default is:

- `.bflow/cases/<domain>-<flow>-smoke.yaml`

Start from `.bflow/cases/templates/test-flow.template.yaml`.
"""


def router_prompt(prefix: str) -> str:
    return f"""# Router Prompt

Use this prompt when you need a single high-level rule set for the `{prefix}` workflow.

```text
You have two browser tools:
- agent_browser: use for exploration and path finding
- chrome_devtools: use for deterministic execution, assertions, screenshots, and diagnostics

Routing rules:
1. If the page path is unknown or unstable, start with `{prefix}-explore`.
2. If the steps are already known, use `{prefix}-replay`.
3. If the user only has a natural-language request and no case file yet, use `{prefix}-new`.
4. If a replay fails, use `{prefix}-diagnose`.
```
"""


def new_prompt(prefix: str) -> str:
    return f"""# {prefix}-new

Use this workflow to create a new case draft from a natural-language test request.

The workflow should:

1. Read `.bflow/cases/templates/test-flow.template.yaml`.
2. Infer a clear case name and output file path under `.bflow/cases/`.
3. Fill any fields that are explicit in the request:
   - `base_url`
   - `goal`
   - `lifecycle`
   - `preconditions`
   - `credentials`
   - `assertions`
   - obvious `steps`
4. Leave uncertain `steps` empty instead of inventing them.
5. Set `lifecycle.stage` to `draft` and `lifecycle.ready_for_replay` to `false`.
6. Create or update the case file.
7. End by recommending `{prefix}-explore` as the next step.
"""


def explore_prompt(prefix: str) -> str:
    return f"""# {prefix}-explore

Use this workflow when a case exists but the exact page path is missing or unstable.

The workflow should:

1. Read the target case file from `.bflow/cases/`.
2. Check the current agent tool configuration first.
3. If `agent-browser` is not available in the current agent, stop immediately and tell the user that this agent is not configured with `agent-browser`.
4. In that stop message, ask the user to install or connect `agent-browser` for the current agent before rerunning `{prefix}-explore`.
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
11. End by recommending `{prefix}-replay`.
"""


def replay_prompt(prefix: str) -> str:
    return f"""# {prefix}-replay

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
"""


def diagnose_prompt(prefix: str) -> str:
    return f"""# {prefix}-diagnose

Use this workflow when `{prefix}-replay` fails.

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
"""


def cases_readme() -> str:
    return """# Case Files

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
"""


def case_template() -> str:
    return """# Unique identifier for the test flow.
# Keep this aligned with the file name.
# Recommended format: snake_case, for example: admin_login_smoke
name: replace_me

# Base URL of the system under test.
# For local development this is often http://localhost:8080
base_url: http://localhost:8080

# The business outcome this test verifies.
# Describe the result, not the full step-by-step instructions.
goal: describe the business goal

# Lifecycle metadata for the flow.
# Recommended stages:
# - draft: the case exists but the route is not confirmed yet
# - ready_for_replay: steps are stable enough for deterministic execution
# - needs_diagnosis: the latest replay failed and needs investigation
#
# Suggested rules:
# - bflow-new sets stage=draft
# - bflow-explore sets stage=ready_for_replay
# - bflow-replay updates last_replayed_at and last_status
# - bflow-diagnose updates last_diagnosed_at
lifecycle:
  stage: draft
  ready_for_replay: false
  last_status: not_run
  last_explored_at: null
  last_replayed_at: null
  last_diagnosed_at: null

# Tool routing. In most cases the defaults are correct:
# - explore: agent_browser
# - replay: chrome_devtools
mode:
  explore: agent_browser
  replay: chrome_devtools

# Conditions that must already be true before the flow starts.
# Examples:
# - current browser state is logged out
# - local service is available
# - test account exists
preconditions:
  - current browser state is logged out

# Optional secrets or identity data used by the flow.
# Leave as {} if the flow does not need credentials.
# Example:
# credentials:
#   username: admin
#   password: 123456
credentials: {}

# The concrete steps to execute.
# If the flow is not mapped out yet, keep this empty and use bflow-explore later.
# Recommended step fields:
# - action: open / type / click / select
# - target: what to interact with
# - value or value_from: input payload if needed
# - expected: what should be visible after the step
steps: []

# The final outcomes that must be true for the flow to pass.
# Write outcomes, not actions.
assertions: []

# Evidence to capture when the flow fails.
# Good defaults:
# - screenshot_on_failure
# - console_logs
# - network_summary
artifacts:
  - screenshot_on_failure
  - console_logs
  - network_summary

# Extra notes, unstable selectors, modal behavior, or known risks.
notes: []
"""


def example_case() -> str:
    return """name: login_admin_smoke
base_url: http://localhost:8080
goal: admin user can log in and enter the admin console
lifecycle:
  stage: ready_for_replay
  ready_for_replay: true
  last_status: not_run
  last_explored_at: null
  last_replayed_at: null
  last_diagnosed_at: null
mode:
  explore: agent_browser
  replay: chrome_devtools
preconditions:
  - current browser state is logged out
  - local service is available
credentials:
  username: admin
  password: 123456
steps:
  - action: open
    target: /login
    expected: login page visible
  - action: type
    target: username input
    value_from: credentials.username
    expected: username field contains value
  - action: type
    target: password input
    value_from: credentials.password
    expected: password field contains value
  - action: click
    target: login button
    expected: authenticated landing page visible
  - action: click
    target: admin console entry
    expected: admin console visible
assertions:
  - admin console title is visible
  - user list is visible
  - no severe console error
artifacts:
  - screenshot_on_failure
  - console_logs
  - network_summary
notes:
  - if a consent modal appears, close it before continuing
"""


def agents_block(prefix: str) -> str:
    return f"""## bflow Workflow

This repository uses `bflow` for browser-test workflows.

Important files:

- `.bflow/README.md`
- `.bflow/prompts/`
- `.bflow/cases/`

If the user types one of these aliases, treat it as a workflow command:

- `/{prefix}-new <request>`: create or update a case draft under `.bflow/cases/`
- `/{prefix}-explore <case-name-or-path>`: use `agent-browser` to discover or refine steps
- `/{prefix}-replay <case-name-or-path>`: use `chrome-devtools` to execute the case
- `/{prefix}-diagnose <case-name-or-path>`: inspect a replay failure

Workflow rules:

1. `/{prefix}-new` creates or updates the case file, keeps `lifecycle.stage=draft`, and ends by recommending `/{prefix}-explore`.
2. `/{prefix}-explore` is for path discovery, not final regression execution, and should promote the case to `ready_for_replay` when the steps are stable.
3. `/{prefix}-replay` runs the saved steps without replanning the business flow and updates replay timestamps/status.
4. `/{prefix}-diagnose` focuses on evidence and root cause, not broad re-exploration, and updates diagnosis metadata.
"""


def copilot_instructions_block(prefix: str) -> str:
    return f"""Use the repository `.bflow/` workflow files for browser-testing tasks.

If the user invokes `/{prefix}-new`, `/{prefix}-explore`, `/{prefix}-replay`, or `/{prefix}-diagnose`, follow the matching workflow and keep the case files in `.bflow/cases/`.
"""


def claude_skill(prefix: str, workflow: str) -> str:
    description = WORKFLOW_METADATA[workflow]["description"]
    argument_hint = WORKFLOW_METADATA[workflow]["argument_hint"]
    body = workflow_body(prefix, workflow, "$ARGUMENTS")
    return f"""---
name: {prefix}-{workflow}
description: {description}
argument-hint: "{argument_hint}"
---

{body}
"""


def opencode_command(prefix: str, workflow: str) -> str:
    description = WORKFLOW_METADATA[workflow]["description"]
    body = workflow_body(prefix, workflow, "$ARGUMENTS")
    return f"""---
description: {description}
---

{body}
"""


def copilot_prompt(prefix: str, workflow: str) -> str:
    description = WORKFLOW_METADATA[workflow]["description"]
    if workflow == "new":
        request_expr = "${input:request:Describe the browser test you want to create}"
    else:
        request_expr = "${input:case:Enter the case name or path}"
    body = workflow_body(prefix, workflow, request_expr)
    return f"""---
agent: agent
description: {description}
---

{body}
"""


def codex_prompt(prefix: str, workflow: str) -> str:
    return workflow_body(prefix, workflow, "$ARGUMENTS") + "\n"


def workflow_body(prefix: str, workflow: str, request_expr: str) -> str:
    example = WORKFLOW_METADATA[workflow]["example"]
    headers = {
        "new": "Create or update a case draft under `.bflow/cases/`.",
        "explore": "Discover or refine the stable browser path for an existing case.",
        "replay": "Execute an existing case with `chrome-devtools`.",
        "diagnose": "Diagnose a failed replay with evidence-first analysis.",
    }
    steps = {
        "new": f"""1. Read `.bflow/README.md` and `.bflow/cases/templates/test-flow.template.yaml`.
2. Infer a concise case name and a file path under `.bflow/cases/`.
3. Fill only the fields that are supported by the request.
4. If the request already includes obvious steps, add them to `steps`.
5. Set `lifecycle.stage` to `draft`, `lifecycle.ready_for_replay` to `false`, and `lifecycle.last_status` to `not_run`.
6. Do not invent missing selectors or paths.
7. Create or update the case file.
8. End by recommending `/{prefix}-explore` for the created case.""",
    "explore": f"""1. Read `.bflow/README.md` and the requested case file under `.bflow/cases/`.
2. Inspect the current agent tool configuration before doing any browser actions.
3. If `agent-browser` is unavailable, stop immediately and tell the user that the current agent is not configured with `agent-browser`.
4. In that stop message, ask the user to install or connect `agent-browser` for the current agent before rerunning `/{prefix}-explore`.
5. Do not silently fall back to `chrome-devtools`, and do not start deterministic replay-style execution in this workflow.
6. Use `agent-browser` to find a stable route for the business goal.
7. Write structured `steps` back into the case file.
8. Update `lifecycle.stage` to `ready_for_replay`, set `lifecycle.ready_for_replay=true`, and write the current ISO 8601 timestamp to `lifecycle.last_explored_at`.
9. Record unstable selectors, modals, redirects, or login-state risks in `notes`.
10. End by recommending `/{prefix}-replay`.""",
        "replay": """1. Read `.bflow/README.md` and the requested case file under `.bflow/cases/`.
2. Use `chrome-devtools` to execute `steps` in order.
3. Do not replan the route unless the case explicitly says exploration is still pending.
4. Check all `assertions`.
5. Write the current ISO 8601 timestamp to `lifecycle.last_replayed_at`.
6. Set `lifecycle.last_status` to `passed` or `failed` based on the outcome.
7. If the flow fails because the saved path is stale, set `lifecycle.stage` to `needs_diagnosis`.
8. Capture requested `artifacts` on failure.
9. Report executed steps, assertion results, and failure evidence.""",
        "diagnose": """1. Read `.bflow/README.md` and the requested case file under `.bflow/cases/`.
2. Focus on the failed step and current page state.
3. Use `chrome-devtools` to inspect console errors, failed requests, missing DOM targets, and blocking overlays.
4. Write the current ISO 8601 timestamp to `lifecycle.last_diagnosed_at` and keep `lifecycle.stage=needs_diagnosis` until the route is fixed.
5. Do not rerun the entire business flow unless the user asks.
6. Report the most likely root cause and the next action.""",
    }
    return f"""# {prefix}-{workflow}

{headers[workflow]}

User input: {request_expr}
Example: /{prefix}-{workflow} {example}

Follow this workflow:

0. If `.bflow/` is missing in the current workspace, stop and tell the user to run `bflow init` in this project first.

{steps[workflow]}
"""


def global_agent_files(prefix: str, agent: str, home_dir: Path) -> dict[Path, str]:
    if agent == "claude":
        files = {}
        for workflow in WORKFLOW_NAMES:
            files[home_dir / ".claude" / "skills" / f"{prefix}-{workflow}" / "SKILL.md"] = claude_skill(prefix, workflow)
        return files
    if agent == "opencode":
        return {
            home_dir / ".config" / "opencode" / "commands" / f"{prefix}-{workflow}.md": opencode_command(prefix, workflow)
            for workflow in WORKFLOW_NAMES
        }
    if agent == "codex":
        return {
            home_dir / ".codex" / "prompts" / f"{prefix}-{workflow}.md": codex_prompt(prefix, workflow)
            for workflow in WORKFLOW_NAMES
        }
    if agent == "copilot":
        prompts_dir = copilot_global_prompts_dir(home_dir)
        return {
            prompts_dir / f"{prefix}-{workflow}.prompt.md": copilot_prompt(prefix, workflow)
            for workflow in WORKFLOW_NAMES
        }
    return {}


def project_agent_files(prefix: str, agent: str) -> dict[str, str]:
    if agent == "claude":
        return {
            f".claude/skills/{prefix}-{workflow}/SKILL.md": claude_skill(prefix, workflow)
            for workflow in WORKFLOW_NAMES
        }
    if agent == "opencode":
        return {
            f".opencode/commands/{prefix}-{workflow}.md": opencode_command(prefix, workflow)
            for workflow in WORKFLOW_NAMES
        }
    if agent == "copilot":
        return {
            f".github/prompts/{prefix}-{workflow}.prompt.md": copilot_prompt(prefix, workflow)
            for workflow in WORKFLOW_NAMES
        }
    if agent == "codex":
        return {}
    return {}


def copilot_global_prompts_dir(home_dir: Path) -> Path:
    if sys.platform == "darwin":
        return home_dir / "Library" / "Application Support" / "Code" / "User" / "prompts"
    if sys.platform.startswith("win"):
        return home_dir / "AppData" / "Roaming" / "Code" / "User" / "prompts"
    return home_dir / ".config" / "Code" / "User" / "prompts"
