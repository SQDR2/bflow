# Case 规范

`cases/` 里的文件不是自然语言描述，而是结构化测试资产。

目标是让你把“和 agent 的一次聊天”沉淀成“以后还能反复执行的测试定义”。

## 推荐字段

```yaml
name: case_name
base_url: http://localhost:8080
goal: short business goal
mode:
  explore: agent_browser
  replay: chrome_devtools
preconditions:
  - condition 1
  - condition 2
credentials:
  username: your_username
  password: your_password
steps:
  - action: open
    target: /login
    expected: login form visible
  - action: type
    target: username input
    value: admin
    expected: username input has value
assertions:
  - target page visible
  - no severe console error
artifacts:
  - screenshot_on_failure
  - console_logs
  - network_summary
notes:
  - unstable point 1
```

## 什么时候写 case

- 流程已经跑通一次之后
- 这个流程后面还要继续测
- 你不想每次都重新手写自然语言步骤

## 如何配合 prompts 使用

### 先探索

把 case 里的 `goal`、`base_url`、`preconditions` 发给 [prompts/explore.md](/home/zlw/github/bflow/prompts/explore.md)，让 `agent-browser` 生成可行步骤。

### 再回放

把 case 的 `steps`、`assertions` 发给 [prompts/replay.md](/home/zlw/github/bflow/prompts/replay.md)，让 `chrome-devtools` 执行。

### 失败后诊断

把失败步骤和现象发给 [prompts/diagnose.md](/home/zlw/github/bflow/prompts/diagnose.md)。
