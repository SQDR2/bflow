# Replay Prompt

适合“步骤已经明确，要严格执行和断言”。

```text
使用 chrome_devtools 按以下步骤执行测试，不要重新规划路径。

测试目标:
{{GOAL}}

环境:
{{BASE_URL}}

前置条件:
{{PRECONDITIONS}}

执行步骤:
{{STEPS}}

断言:
{{ASSERTIONS}}

执行规则:
1. 严格按步骤执行。
2. 每一步执行后检查预期结果。
3. 如果页面上的功能、按钮语义、跳转去向或交互条件不明确，先暂停浏览器动作，到工作区代码中定位对应源码，弄清楚含义后再继续当前步骤。
4. 代码回查只用于澄清当前步骤或断言，不要把 replay 退化成新的路径探索。
5. 如果失败，立即记录:
   - failed_step
   - report_path: .bflow/reports/<case-name>.latest.md
   - screenshot suggestion
   - console summary
   - network summary
6. 把失败摘要、证据、下一步建议写入 `.bflow/reports/<case-name>.latest.md`，并把 case 的 `lifecycle.last_failure_report` 指向它。
7. 如果用了代码回查，补充记录相关代码证据摘要。
8. 关键提交动作前后记录 network 状态。
9. 不要因为页面变化而自行改写业务目标。

输出格式:
{
  "case": "...",
  "status": "passed|failed",
  "report_path": ".bflow/reports/<case-name>.latest.md|null",
  "executed_steps": [],
  "assertions": {},
  "artifacts": {},
  "code_context": [],
  "root_cause_hint": ""
}
```

## 示例

```text
使用 chrome_devtools 按以下步骤执行测试，不要重新规划路径。

测试目标:
验证管理员可以登录并进入管理平台

环境:
http://localhost:8080

前置条件:
- 当前未登录

执行步骤:
1. 打开 /login
2. 输入账号 admin
3. 输入密码 123456
4. 点击“登录”
5. 点击“管理平台”

断言:
- 页面出现“管理平台”标题
- 用户列表可见
- 无严重 console error
```
