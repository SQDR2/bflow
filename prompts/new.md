# New Case Prompt

适合“我先给一句业务描述，你帮我生成一个新的 case 草稿文件”。

```text
你的任务不是执行测试，而是创建一个新的 case 草稿。

输入是一段自然语言测试需求。你需要基于 `cases/templates/test-flow.template.yaml` 的结构，生成一个新的 `cases/*.yaml` 文件草稿。

处理规则:
1. 根据需求推断一个清晰、可复用的 case 名称。
2. case 文件名使用 kebab-case，推荐格式:
   <domain>-<flow>-<type>.yaml
3. 根据描述尽量填写这些字段:
   - name
   - base_url
   - goal
   - preconditions
   - credentials
   - steps
   - assertions
   - artifacts
   - notes
4. 如果描述里已经给出了明确步骤，就把这些步骤初步写入 `steps`。
5. 如果步骤不完整，不要乱编造；可以保留 `steps: []`，或者只写确定的步骤。
6. 生成完成后，输出:
   - 建议创建的文件路径
   - 生成的 YAML 内容
   - 哪些字段是根据输入直接得到的
   - 哪些字段仍然需要后续补充
7. 最后明确建议用户下一步执行 `explore`，用于验证并补全稳定步骤。

输出要求:
- 不要直接执行测试
- 不要直接进入回放
- 当前阶段只负责创建 case 草稿
```

## 推荐输入方式

```text
新增一个测试流程：
访问 localhost:8080，使用 admin / 123456 登录，点击管理平台，检查用户列表是否显示。
```

## 期望输出示例

```text
建议文件路径:
cases/admin-login-smoke.yaml

YAML:
name: admin_login_smoke
base_url: http://localhost:8080
goal: admin user can log in and open admin console
mode:
  explore: agent_browser
  replay: chrome_devtools
preconditions:
  - current browser state is logged out
credentials:
  username: admin
  password: 123456
steps:
  - action: open
    target: /
    expected: home page or login page visible
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
    expected: authenticated page visible
  - action: click
    target: admin console entry
    expected: admin console visible
assertions:
  - admin console title is visible
  - user list is visible
artifacts:
  - screenshot_on_failure
  - console_logs
  - network_summary
notes:
  - next step: run explore to verify the actual stable path

建议下一步:
请继续使用 explore prompt，让 agent_browser 验证并补全这条流程的稳定步骤。
```
