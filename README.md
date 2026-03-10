# bflow

[中文文档](./README.zh-CN.md)

`bflow` is a browser-test workflow installer for multiple coding agents.

It does not run a browser or execute tests by itself. Its job is to install a shared workflow library into your project and generate agent-specific entry points, such as:

- `/bflow-new`
- `/bflow-explore`
- `/bflow-replay`
- `/bflow-diagnose`

These commands map to the following workflow stages:

1. `new`
   - Create a case draft from a natural-language request
2. `explore`
   - Use `agent-browser` to discover or refine the stable path
3. `replay`
   - Use `chrome-devtools` to execute the saved steps
4. `diagnose`
   - Inspect replay failures with console, network, and DOM evidence

## What `bflow init` Creates

Running `bflow init` in a project creates a shared `.bflow/` directory:

```text
.bflow/
├── README.md
├── config.json
├── prompts/
│   ├── router.md
│   ├── new.md
│   ├── explore.md
│   ├── replay.md
│   └── diagnose.md
└── cases/
    ├── README.md
    ├── templates/
    │   └── test-flow.template.yaml
    └── examples/
        └── login-admin-smoke.yaml
```

This `.bflow/` directory is the project-local workflow library.

`bflow` also installs project-local agent adapter files based on the agents you choose. This is intentional because all `bflow-*` commands rely on the current workspace `.bflow/` directory.

- `Claude Code`
  - `.claude/skills/`
- `OpenCode`
  - `.opencode/commands/`
- `GitHub Copilot`
  - `.github/prompts/` and `.github/copilot-instructions.md`
- `Codex`
  - `AGENTS.md`

## Prerequisites

Before you use replay or diagnose workflows in any target agent, install `chrome-devtools-mcp` in that agent first:

- https://github.com/ChromeDevTools/chrome-devtools-mcp

If you want to use exploration workflows, make sure your target agent also has access to your `agent-browser` integration.

## Install

The quickest way to try `bflow` is to run it directly without installing anything:

```bash
python -m bflow --help
python -m bflow init
python -m bflow doctor
```

If you want a local editable install, use a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

If you want a global CLI without touching the system Python environment, use `pipx`:

```bash
pipx install --editable .
```

On Arch Linux and other distributions that enforce PEP 668, `pip install -e .` may fail in the system Python environment with `externally-managed-environment`. In that case, use either:

- direct module execution: `python -m bflow ...`
- a virtual environment
- `pipx install --editable .`

## Commands

### `bflow init`

Initialize the current project.

Interactive:

```bash
bflow init
```

Non-interactive:

```bash
bflow init --agents claude,opencode,copilot,codex --prefix bflow
```

### `bflow update`

Regenerate files from `.bflow/config.json`.

```bash
bflow update
```

### `bflow agents`

List supported agent adapters.

```bash
bflow agents
```

### `bflow doctor`

Check whether the current project still contains the files that `bflow init` generated.

```bash
bflow doctor
```

## Interactive Init Experience

When you run `bflow init` without explicit flags, it enters interactive mode.

It asks for:

1. Target agents
2. Command prefix, such as `bflow`
3. A final confirmation summary before writing files

After installation, it prints a grouped summary:

- Shared workflow files
- Project adapter files
- Warnings

You can also run `bflow doctor` later to verify that the generated files are still present.

## Recommended Usage

After initialization, restart the target agent UI if it only loads slash commands on startup.

Then use the workflow in this order:

### 1. Create a New Flow

```text
/bflow-new visit localhost:8080, sign in with admin / 123456, open the admin console, and verify the user list is visible
```

Expected result:

- a new case draft is created under `.bflow/cases/`
- obvious facts are filled into the case fields
- uncertain `steps` are left empty instead of guessed
- the workflow ends by recommending `/bflow-explore`

### 2. Explore the Real Path

```text
/bflow-explore admin-login-smoke
```

Expected result:

- `agent-browser` discovers or refines the actual route on the current page version
- if the current agent does not have `agent-browser`, the workflow should stop immediately and tell the user to install or connect it for that agent
- it should not silently fall back to `chrome-devtools` during exploration
- the case file is updated with structured `steps`
- the case lifecycle is promoted to `ready_for_replay`
- unstable selectors, modals, or redirect risks are recorded in `notes`

### 3. Replay the Stable Flow

```text
/bflow-replay admin-login-smoke
```

Expected result:

- `chrome-devtools` executes the saved `steps` in order
- assertions are checked
- replay timestamps and the last result are written into `lifecycle`
- failure evidence is captured when needed

### 4. Diagnose a Failure

```text
/bflow-diagnose admin-login-smoke
```

Expected result:

- focus stays on the failed step instead of rerunning the whole flow
- console, network, and DOM evidence is summarized
- diagnosis timestamps are written into `lifecycle`
- the next repair action is suggested

## Generated File Responsibilities

### `.bflow/prompts/`

This directory stores workflow source instructions, not business test data.

- `new.md`
  - builds a case draft
- `explore.md`
  - discovers or refines steps
- `replay.md`
  - executes the saved steps
- `diagnose.md`
  - inspects failures
- `router.md`
  - contains high-level routing rules

### `.bflow/cases/`

This directory stores reusable browser-test assets for the project.

- `templates/test-flow.template.yaml`
  - starting template for a new flow
- `examples/login-admin-smoke.yaml`
  - full reference example

Each case also contains a `lifecycle` block so the workflow can track whether the flow is still a draft, ready for replay, or waiting for diagnosis.

### `AGENTS.md`

This is the project-level fallback instruction file. It matters for agent surfaces that rely more on repository guidance than native slash commands.

## When to Add a New Case File

Add a new file under `.bflow/cases/` when you introduce a new business flow.

Examples:

- `.bflow/cases/auth-login-smoke.yaml`
- `.bflow/cases/orders-search-smoke.yaml`
- `.bflow/cases/admin-user-list-regression.yaml`

In most cases you do not need to add a new prompt file. The four built-in workflows are intended to be reused.

## Development

Run tests:

```bash
python -m unittest discover -s tests -v
```

List supported adapters:

```bash
python -m bflow agents
```

Run installation checks:

```bash
python -m bflow doctor
```

## Reference Documents in This Repo

- [Chinese README](./README.zh-CN.md)
- [agent-browser-chrome-devtools-guide.md](/home/zlw/github/bflow/agent-browser-chrome-devtools-guide.md)
- [prompts/new.md](/home/zlw/github/bflow/prompts/new.md)
- [cases/templates/test-flow.template.yaml](/home/zlw/github/bflow/cases/templates/test-flow.template.yaml)
