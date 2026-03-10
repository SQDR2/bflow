# agent-browser 安装与接入指南

这份文档说明如何在当前项目里把 `agent-browser` 配好给 bflow 使用。

## 为什么需要两层安装

`agent-browser` 本体是浏览器自动化 CLI，不是 MCP server。

要让 `/bflow-explore` 真正可用，需要同时满足：

1. 本机有 `agent-browser` 可执行命令
2. 当前 AI agent 已安装 `agent-browser` skill，知道如何调用它
3. 当前项目已经执行过 `bflow init`，存在 `.bflow/`

缺任何一层，`/bflow-explore` 都不应继续执行探索。

## 1. 安装 agent-browser CLI

推荐全局安装：

```bash
npm install -g agent-browser
agent-browser install
```

Linux 若缺少系统依赖，可执行：

```bash
agent-browser install --with-deps
```

## 2. 在当前项目里为目标 agent 安装 skill

请在**当前项目根目录**执行。针对本项目当前选择的 agent，推荐命令如下：

- Codex: `npx skills add vercel-labs/agent-browser --skill agent-browser --agent codex -y`

如果你想给更多 agent 一起安装，也可以分别执行对应命令。

## 3. 安装后应看到什么

成功后，当前项目里通常会出现：

- `.agents/skills/agent-browser/SKILL.md`
- `.agents/skills/agent-browser/references/`
- `skills-lock.json`

## 4. 验证

先确认 CLI 可用：

```bash
agent-browser --help
```

再确认当前项目里 skill 已安装：

```bash
find .agents/skills/agent-browser -maxdepth 2 -type f
```

最后重启当前 agent UI，再执行：

```text
/bflow-explore <case-name>
```

## 5. 在 bflow 里的使用顺序

1. 在项目根目录执行 `bflow init`
2. 安装 `agent-browser` CLI
3. 在项目根目录安装对应 agent 的 `agent-browser` skill
4. 重启 agent UI
5. 先执行 `/bflow-new` 创建 case
6. 再执行 `/bflow-explore` 让 `agent-browser` 发现稳定路径
7. 最后执行 `/bflow-replay` 用 `chrome-devtools` 做确定性回放
