# Explore Prompt

适合“我知道目标，但不想手写每一步”。

```text
先使用 agent_browser 探索目标流程，不要直接结束。

探索目标:
{{GOAL}}

环境:
{{BASE_URL}}

前置条件:
{{PRECONDITIONS}}

探索要求:
1. 找到一条可行且尽量短的业务路径。
2. 不要只给结论，必须输出结构化步骤。
3. 每一步都包含:
   - step
   - page
   - action
   - target_hint
   - input_value (如有)
   - expected
   - risk
4. 标出不稳定点，例如:
   - 文案可能变化
   - 弹窗可能出现
   - 依赖登录状态
5. 探索完成后，不要自动自由发挥执行其他目标。

输出格式:
{
  "goal": "...",
  "steps": [],
  "assertions": [],
  "risks": []
}
```

## 示例

```text
先使用 agent_browser 探索目标流程，不要直接结束。

探索目标:
验证管理员可以登录并进入管理平台

环境:
http://localhost:8080

前置条件:
- 当前未登录
- 使用账号 admin
- 使用密码 123456
```
