# bflow

[English README](./README.md)

`bflow` 是一个面向多种 coding agent 的浏览器测试工作流安装器。

它本身不负责启动浏览器或执行测试。它的职责是把一套统一的工作流安装到你的项目里，并为不同 agent 生成对应的命令入口，例如：

- `/bflow-new`
- `/bflow-explore`
- `/bflow-replay`
- `/bflow-diagnose`

这四个命令分别对应下面四个阶段：

1. `new`
   - 根据自然语言需求创建 case 草稿
2. `explore`
   - 使用 `agent-browser` 探索或修正稳定路径
3. `replay`
   - 使用 `chrome-devtools` 执行已保存的步骤
4. `diagnose`
   - 在回放失败后收集 console、network 和 DOM 证据

## `bflow init` 会生成什么

在项目里执行 `bflow init` 后，会生成一个共享的 `.bflow/` 目录：

```text
.bflow/
├── README.md
├── agent-browser-setup.md
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

这个 `.bflow/` 目录就是项目级的工作流资产库。

其中 `.bflow/agent-browser-setup.md` 会集中记录当前项目里 `agent-browser` 的 CLI 安装、skills 安装、验证方式以及与 `bflow-explore` 的配合用法。

同时，`bflow` 会按你选择的 agent 写入项目内的适配文件。这样设计是刻意的，因为所有 `bflow-*` 指令都依赖当前工作区里的 `.bflow/` 目录。

- `Claude Code`
  - `.claude/skills/`
- `OpenCode`
  - `.opencode/commands/`
- `GitHub Copilot`
  - `.github/prompts/` 和 `.github/copilot-instructions.md`
- `Codex`
  - `AGENTS.md`

## 前置依赖

在任意目标 agent 中使用 replay 或 diagnose 工作流之前，请先在该 agent 里安装 `chrome-devtools-mcp`：

- https://github.com/ChromeDevTools/chrome-devtools-mcp

如果你还要使用 explore 工作流，请确保对应 agent 也已经接入了 `agent-browser`。

## 安装

最快的试用方式其实是不安装，直接运行：

```bash
python -m bflow --help
python -m bflow init
python -m bflow doctor
```

如果你希望本地可编辑安装，推荐先创建虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

如果你希望安装成全局 CLI，但又不想污染系统 Python，推荐使用 `pipx`：

```bash
pipx install --editable .
```

在 Arch Linux 或其他启用了 PEP 668 的系统里，直接执行 `pip install -e .` 可能会报 `externally-managed-environment`。这不是项目本身的问题，而是系统 Python 不允许你直接写入包。

这时请改用下面任一方式：

- 直接运行模块：`python -m bflow ...`
- 使用虚拟环境
- 使用 `pipx install --editable .`

## 命令

### `bflow init`

初始化当前项目。

交互式：

```bash
bflow init
```

非交互式：

```bash
bflow init --agents claude,opencode,copilot,codex --prefix bflow
```

### `bflow update`

根据 `.bflow/config.json` 重新生成文件。

```bash
bflow update
```

### `bflow agents`

列出支持的 agent 适配器。

```bash
bflow agents
```

### `bflow doctor`

检查当前项目里，`bflow init` 生成的文件是否仍然存在。

```bash
bflow doctor
```

## 交互式初始化体验

`bflow init` 在未传入参数时会进入交互模式。

它会依次让你选择：

1. 目标 agent 列表
2. 命令前缀，例如 `bflow`
3. 安装前确认摘要

安装完成后，它会按下面几类打印结果：

- 共享工作流文件
- 项目级适配文件
- 警告信息

后续你也可以执行 `bflow doctor` 来检查生成文件是否还完整。

## 推荐使用方式

初始化完成后，如果你的 agent 只在启动时加载 slash commands，请先重启。

然后按下面的顺序使用：

### 1. 新建流程

```text
/bflow-new 访问 localhost:8080，使用 admin / 123456 登录，点击管理平台，并检查用户列表是否显示
```

预期结果：

- 在 `.bflow/cases/` 下生成一个新的 case 草稿
- 明确的信息会被直接填入字段
- 不确定的 `steps` 会保留为空，而不是乱猜
- 最后会推荐你执行 `/bflow-explore`

### 2. 探索真实路径

```text
/bflow-explore admin-login-smoke
```

预期结果：

- `agent-browser` 负责发现或修正当前版本页面下的实际路径
- 执行前会先读取 `.bflow/config.json` 和 `.bflow/agent-browser-setup.md`，校验当前 agent 是否已按配置接入 `agent-browser`
- 如果当前 agent 没有接入 `agent-browser`，应立即中止，并按照当前 agent 配置返回明确的安装或切换指引
- 不应静默退化为直接使用 `chrome-devtools` 或 `chrome-devtools-mcp` 执行探索流程
- case 文件会写入结构化的 `steps`
- case 的 `lifecycle` 会被提升到 `ready_for_replay`
- 不稳定的选择器、弹窗、重定向风险会记录到 `notes`

### 3. 回放稳定流程

```text
/bflow-replay admin-login-smoke
```

预期结果：

- `chrome-devtools` 按 `steps` 顺序执行
- 校验 `assertions`
- 回放时间戳和最近一次结果会写入 `lifecycle`
- 失败时采集证据

### 4. 排查失败

```text
/bflow-diagnose admin-login-smoke
```

预期结果：

- 聚焦失败步骤而不是整条链路重跑
- 汇总 console、network 和 DOM 证据
- 诊断时间戳会写入 `lifecycle`
- 给出下一步修复建议

## 生成文件的职责

### `.bflow/prompts/`

这里存的是工作流源说明，不是业务测试数据。

- `new.md`
  - 负责根据自然语言需求生成 case 草稿
- `explore.md`
  - 负责探索或修正步骤
- `replay.md`
  - 负责执行保存下来的步骤
- `diagnose.md`
  - 负责分析失败
- `router.md`
  - 负责高层路由规则

### `.bflow/cases/`

这里存的是项目可复用的浏览器测试资产。

- `templates/test-flow.template.yaml`
  - 新流程的起点模板
- `examples/login-admin-smoke.yaml`
  - 完整参考示例

每个 case 现在还会包含一个 `lifecycle` 字段，用来记录当前流程是草稿、可回放还是待诊断状态。

### `AGENTS.md`

这是项目级的回退规则文件。对于更依赖仓库规则而不是 slash command 的 agent 表面，它很重要。

## 什么时候要新增 case 文件

当你要引入一个新的业务流程时，就应该在 `.bflow/cases/` 下新增一个文件。

例如：

- `.bflow/cases/auth-login-smoke.yaml`
- `.bflow/cases/orders-search-smoke.yaml`
- `.bflow/cases/admin-user-list-regression.yaml`

大多数情况下，你不需要新增 prompt 文件。内置的四个工作流就是为了复用而设计的。

## 开发

运行测试：

```bash
python -m unittest discover -s tests -v
```

查看支持的 adapter：

```bash
python -m bflow agents
```

执行安装检查：

```bash
python -m bflow doctor
```

## 仓库中的参考文档

- [English README](./README.md)
- [agent-browser-chrome-devtools-guide.md](/home/zlw/github/bflow/agent-browser-chrome-devtools-guide.md)
- [prompts/new.md](/home/zlw/github/bflow/prompts/new.md)
- [cases/templates/test-flow.template.yaml](/home/zlw/github/bflow/cases/templates/test-flow.template.yaml)
