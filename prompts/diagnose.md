# Diagnose Prompt

适合“测试失败后定位问题”。

```text
使用 chrome_devtools 对失败步骤做诊断，不要重新跑完整业务流程，除非我明确要求。

诊断目标:
{{GOAL}}

环境:
{{BASE_URL}}

失败上下文:
{{FAILURE_CONTEXT}}

诊断要求:
1. 优先查看页面当前状态。
2. 收集并总结:
   - console errors
   - failed requests / 4xx / 5xx
   - DOM 是否缺失关键元素
   - 是否存在遮罩、弹窗、权限拦截、跳转异常
3. 如果页面功能语义、条件渲染、权限逻辑或接口行为仍然不明确，继续到工作区代码里定位相关源码，再回到当前失败点做判断。
4. 代码回查只服务于当前失败原因定位，不要把 diagnose 扩展成新的全链路探索。
5. 如果有必要，再补充截图建议。
6. 输出最可能的根因、用到的代码证据和建议下一步。
7. 除非页面路径已经明显失效，否则不要回到自由探索模式。

输出格式:
{
  "status": "diagnosed",
  "failed_step": "...",
  "console_summary": [],
  "network_summary": [],
  "dom_findings": [],
  "code_findings": [],
  "root_cause_hint": "",
  "next_action": ""
}
```

## 示例

```text
使用 chrome_devtools 对失败步骤做诊断，不要重新跑完整业务流程，除非我明确要求。

诊断目标:
管理员登录后点击“管理平台”没有进入目标页面

环境:
http://localhost:8080

失败上下文:
- 登录已成功
- 点击“管理平台”后页面无变化
- 需要检查 console、network 和目标元素是否存在
```
