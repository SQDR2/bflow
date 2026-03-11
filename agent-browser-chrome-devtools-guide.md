# agent-browser + chrome-devtools-mcp: 更友好的自定义测试流程设计

## 1. 先说结论

如果你的目标是“让 AI 帮你跑浏览器测试”，最实用的做法不是把 `agent-browser` 和 `chrome-devtools-mcp` 当成两个同质工具一起乱用，而是给它们分工：

- `agent-browser` 负责“会思考的探索和执行”
- `chrome-devtools-mcp` 负责“可验证、可观测、可诊断的精确控制”

最稳的组合方式是：

1. 先用 `agent-browser` 探路，找出一条当前页面结构下可走通的业务路径。
2. 把这条路径沉淀成结构化测试步骤，而不是只保留自然语言结论。
3. 再用 `chrome-devtools-mcp` 做确定性的回放、断言和诊断。
4. 失败时优先回到 `chrome-devtools-mcp` 看 DOM、console、network、performance，再决定是否重新让 `agent-browser` 探索。

这比“一个任务里让两个 MCP 都随便出手”更稳定，也更容易复用。

## 2. 两个工具分别适合做什么

### agent-browser

`agent-browser` 来自 Vercel Labs，底层依赖 Browserbase 和 Stagehand，定位是让模型可以直接完成网页任务，比如：

- 打开页面并理解页面结构
- 根据页面变化自适应点击、输入、导航
- 提取信息
- 执行多步骤网页操作

它的优势是：

- 对“页面会变、按钮文案会变、布局会变”的场景更友好
- 更接近“让代理完成任务”而不是“手写每一步自动化脚本”
- 对探索型任务、原型验证、冒烟路径验证很合适

它的短板也很明显：

- 可重复性通常不如显式脚本或显式断言
- 如果你没有把结果结构化，后续很难沉淀为稳定测试资产
- 更适合“找到路径”，不适合单独承担全部精确校验

### chrome-devtools-mcp

`chrome-devtools-mcp` 是 Chrome DevTools 官方出的 MCP server，本质上是把 DevTools 能力暴露给模型。它更适合：

- 打开/切换标签页
- 点击、输入、截图
- 读取 DOM 和可访问性树
- 采集 console、network、performance
- 做更精细的调试和诊断

它的优势是：

- 更可控
- 更适合做显式断言
- 出错后更容易定位根因
- 很适合“回放、验收、诊断”

它的短板是：

- 对“模糊目标”不如 agent 型工具自然
- 如果页面变化很大，纯靠它让模型临场找路径，效率通常不如 `agent-browser`

## 3. 最推荐的协作模型

## 3.1 不要一开始就强求“同一个浏览器会话双控”

从官方资料看：

- `agent-browser` 主要运行在 Browserbase 托管浏览器会话上，并能返回 `session_id`、`live_view_url`、`debugger_fullscreen_url`
- `chrome-devtools-mcp` 主要连接本地或指定调试端口的 Chrome 实例

所以更合理的默认假设是：

- 两者“能力互补”很强
- 但“天然共享同一个实时浏览器会话”并不是默认工作模式

这意味着更好的工程策略不是强行把它们绑成一个控制面，而是把它们做成两个阶段：

- 阶段 A：`agent-browser` 负责探索
- 阶段 B：`chrome-devtools-mcp` 负责验证和诊断

这条边界很重要。它会直接决定你的流程是否稳定。

## 3.2 用“两阶段测试流”替代“一次性大 Prompt”

推荐工作流如下：

### 阶段 A：探索

目标：

- 找到当前页面版本下的可行业务路径
- 记录关键页面、关键动作、关键选择器线索、关键校验点

交给 `agent-browser` 的任务应该像这样：

> 访问站点并完成登录到下单的最短路径。不要只给结论，输出结构化步骤，包括每一步的页面目的、操作对象、可替代定位线索、预期结果和失败点。

如果当前 agent 根本没有接入 `agent-browser`，更合理的处理方式不是偷偷退化为 `chrome-devtools-mcp` 顶上，而是直接中止探索阶段，明确告诉用户：当前 agent 缺少 `agent-browser` 配置，需要先接入后再执行探索。

产出不是“我已经测过了”，而应该是结构化结果，例如：

```json
{
  "goal": "guest checkout smoke test",
  "steps": [
    {
      "page": "home",
      "action": "click",
      "target_hint": "header search input",
      "expected": "search panel visible"
    },
    {
      "page": "search",
      "action": "type",
      "target_hint": "search input",
      "value": "running shoes",
      "expected": "product list visible"
    }
  ],
  "assertions": [
    "cart badge increments to 1",
    "checkout button visible",
    "order submit response is 200 or 201"
  ],
  "risks": [
    "login modal may appear depending on cookie state"
  ]
}
```

### 阶段 B：回放和断言

目标：

- 用 `chrome-devtools-mcp` 严格执行上一步沉淀的步骤
- 每一步有明确断言
- 收集 console、network、screenshot、performance 等证据

交给 `chrome-devtools-mcp` 的任务应该更明确：

> 按以下结构化步骤执行，不要重新规划业务路径。每一步执行后检查预期 UI 状态；提交动作前后记录 network；失败时截图并导出 console errors。

这一步的重点是：

- 不要让模型重新“自由发挥”
- 让它按规范执行
- 让失败结果可诊断

这里还可以再补一条很实用的规则：

> 如果 `chrome-devtools-mcp` 在回放或诊断时，遇到页面功能语义不清楚、按钮文案和实际行为对不上、或者某个区域为什么显示/不显示暂时看不明白，不要立刻瞎猜，也不要立刻切回 `agent-browser` 重新探索；应该先暂停浏览器动作，到当前工作区里查对应源码，弄清楚这个功能真正是什么意思，再继续当前阶段。

这样做的价值是：

- 保持 `replay` / `diagnose` 仍然是“验证和定位”阶段
- 用代码语义补足页面表象看不清的问题
- 减少因为 UI 文案歧义导致的误判
- 避免每次遇到不确定点都回退成整条链路重探

比较适合回查的代码包括：

- 当前页面对应的路由定义
- 触发按钮或菜单项对应的组件源码
- 控制显隐的权限判断、feature flag、条件渲染逻辑
- 点击后触发的请求封装、mutation、action、store 更新逻辑
- 页面文案、国际化 key、状态映射表

不适合做的事情是：

- 因为看到代码里还有别的入口，就擅自改写 case 目标
- 把一次小范围代码回查扩展成新的自由探索任务
- 在还没核对当前步骤的前提下，直接按想象修改后续路径

## 4. 更友好的调用方式

如果你想让日常使用更顺手，核心不是继续堆 Prompt，而是做三层封装。

## 4.1 第一层：MCP 只负责能力暴露

把两个 server 都接进同一个客户端，但命名要清晰：

- `agent_browser`
- `chrome_devtools`

参考配置可以像这样：

```json
{
  "mcpServers": {
    "agent_browser": {
      "command": "npx",
      "args": ["@browserbasehq/mcp@latest"],
      "env": {
        "BROWSERBASE_API_KEY": "YOUR_BROWSERBASE_API_KEY",
        "BROWSERBASE_PROJECT_ID": "YOUR_PROJECT_ID"
      }
    },
    "chrome_devtools": {
      "command": "npx",
      "args": ["chrome-devtools-mcp@latest"]
    }
  }
}
```

如果你需要让 `chrome-devtools-mcp` 连接现有 Chrome，可再补充参数，例如 `--browserUrl` 或 `--chromePath`。

## 4.2 第二层：写一个“工具路由 Prompt”

这是最值得做的部分。你需要明确告诉模型什么场景该用哪个工具。

可以直接保存成一个固定模板：

```text
你同时拥有 agent_browser 和 chrome_devtools 两个 MCP 工具。

路由规则：
1. 当任务目标模糊、页面路径未知、页面可能变化时，优先使用 agent_browser 探索。
2. 当任务需要显式断言、抓取 console/network/performance、输出可复现证据时，优先使用 chrome_devtools。
3. 不要在一次执行中频繁在两个工具间来回切换，除非上一个阶段已经产出结构化步骤。
4. 当 chrome_devtools 在执行阶段遇到功能语义不清的页面元素时，可以暂停浏览器动作，先去代码里找到相关实现，再回来继续当前步骤。
5. 所有浏览器任务都必须输出：
   - 执行步骤
   - 页面状态
   - 断言结果
   - 失败原因
   - 下一步建议
```

这类“路由 Prompt”比给模型一句“帮我测一下”有用得多。

## 4.3 第三层：把测试需求写成结构化 Case，而不是口语需求

最适合长期复用的方式，是给模型一个统一测试描述格式。比如：

```yaml
name: checkout_smoke
base_url: https://example.com
goal: guest user can search product and submit checkout
mode:
  explore: agent_browser
  replay: chrome_devtools
preconditions:
  - user is logged out
  - cart is empty
steps:
  - action: open
    target: /
    expected: home page visible
  - action: search
    target: running shoes
    expected: product list visible
  - action: add_to_cart
    target: first product
    expected: cart count becomes 1
  - action: checkout
    expected: checkout page visible
assertions:
  - no console error
  - checkout submit response status in [200,201,302]
artifacts:
  - screenshot_on_failure
  - console_logs
  - network_summary
  - performance_trace_on_checkout
```

这样做的收益是：

- 换模型也能用
- 换 MCP client 也能用
- 你能把 case 沉淀到仓库里
- 后续可以半自动转换成 Playwright/Cypress/自研 runner

## 5. 适合落地的三种测试模式

## 5.1 探索模式

适合：

- 新站点
- 页面频繁变化
- 需求刚成形
- 没有稳定选择器

推荐做法：

- 只让 `agent-browser` 先跑通主路径
- 强制输出结构化步骤
- 不在这个阶段追求全量断言

一句话理解：

先找路，不先抠细节。

## 5.2 回归模式

适合：

- 已经有稳定流程
- 每次上线都要验证主链路
- 需要可重复执行

推荐做法：

- 使用上次探索沉淀下来的结构化步骤
- 主要用 `chrome-devtools-mcp` 执行
- 每一步都带断言和失败证据

一句话理解：

先固定打法，再追求稳定重复。

## 5.3 诊断模式

适合：

- 页面报错
- 请求异常
- 某一步偶发失败
- 性能退化

推荐做法：

- 直接用 `chrome-devtools-mcp`
- 优先抓 console、network、performance
- 必要时再让 `agent-browser` 重新探索是否页面路径变化

一句话理解：

先定位根因，不先重跑全流程。

## 6. 一套更顺手的日常工作法

如果你想真正“更方便地使用”，建议你把日常调用固定成下面这套习惯。

### 习惯 1：每个测试任务都拆成四段

- 目标
- 前置条件
- 步骤
- 断言

不要只写：

> 帮我测一下支付流程

应该写成：

> 验证未登录用户从商品页加入购物车并进入结算页。前置条件是空购物车。输出步骤、断言、失败截图、console 和 network 摘要。

### 习惯 2：把“探索结果”保存下来

每次 `agent-browser` 跑通后，都把结果沉淀为：

- case 文件
- 关键 selector/hint 列表
- 已知不稳定点

否则你每次都在重复花 token 让模型重新理解网站。

### 习惯 3：把“证据采集”默认打开

至少保留：

- 失败截图
- console errors
- 关键请求摘要

如果是提交、支付、登录、搜索这类关键链路，再补：

- 性能 trace
- 页面快照

### 习惯 4：把“重新规划路径”和“按步骤执行”分开

这是最常见的稳定性问题来源。

当你说：

> 帮我完成这个测试，并且自动修正所有流程变化

模型会一直重规划。结果往往是：

- 复现困难
- 断言不稳定
- 成败不可比

更好的做法是：

- 探索任务允许规划
- 回归任务禁止规划

## 7. 我最建议你采用的最小闭环

如果你现在就想开始，而不是先做很重的工程化，我建议直接用这条最小闭环：

1. 在 MCP client 里同时接入 `agent-browser` 和 `chrome-devtools-mcp`
2. 先让 `agent-browser` 为一个核心业务流程生成结构化步骤
3. 把步骤保存成 `yaml/json` case
4. 再让 `chrome-devtools-mcp` 按 case 执行，并输出断言和证据
5. 失败后只在诊断阶段使用 `chrome-devtools-mcp`
6. 页面变化明显时，才重新回到 `agent-browser` 探索

这条链路已经足够覆盖大多数：

- 冒烟测试
- 回归测试
- 页面故障定位
- 上线后巡检

## 8. 一个可以直接复用的提示词模板

下面这版模板适合日常直接用。

```text
请帮我执行一个浏览器测试任务。

工具使用规则：
- 如果页面路径未知或页面结构可能变化，先用 agent_browser 探索。
- 一旦探索出步骤，输出结构化步骤，不要直接结束。
- 结构化步骤确认后，使用 chrome_devtools 执行回放和断言。
- 回放阶段不要自行改写业务目标。
- 如果失败，输出失败步骤、截图建议、console 摘要、network 摘要和可能根因。

测试任务：
目标：验证访客用户可以搜索商品并进入结算页
前置条件：未登录，购物车为空
断言：
- 商品列表出现
- 加购后购物车数量为 1
- 结算页成功展示
- 无严重 console error
- 关键请求无 5xx
产物：
- 结构化步骤
- 执行结果
- 失败证据
```

## 9. 如果你要继续往前做工程化

下一步最值得做的，不是继续调 Prompt，而是做下面三件事：

### 方向 1：维护一份 case 库

按业务维护：

- `login_smoke.yaml`
- `checkout_smoke.yaml`
- `search_regression.yaml`

### 方向 2：维护一份 prompt 库

至少准备三个固定模板：

- 探索模板
- 回放模板
- 诊断模板

### 方向 3：把输出统一为测试报告格式

例如统一输出：

```json
{
  "case": "checkout_smoke",
  "status": "failed",
  "failed_step": "submit checkout",
  "assertions": {
    "checkout_page_visible": true,
    "no_console_error": false
  },
  "artifacts": {
    "screenshot": "artifacts/checkout-failed.png",
    "console": "artifacts/console.json",
    "network": "artifacts/network.json"
  },
  "root_cause_hint": "POST /api/checkout returned 500"
}
```

这一步做完，你的浏览器测试就不再只是“和 AI 聊天”，而会开始变成“可沉淀的测试系统”。

## 10. 参考结论

基于这三个来源，我的建议可以压缩成一句话：

`agent-browser` 用来找路，`chrome-devtools-mcp` 用来验路和查错；不要一上来就把两者混成一个自由执行体，而应该把它们放进“探索 -> 结构化 -> 回放 -> 诊断”的流水线里。

## 11. 参考来源

- Vercel Labs `agent-browser`: https://github.com/vercel-labs/agent-browser
- Chrome 官方 `chrome-devtools-mcp`: https://github.com/ChromeDevTools/chrome-devtools-mcp
- 文章：使用 Codex + MCP 的实践记录: https://www.cnblogs.com/gyc567/p/19494426

## 12. 补充说明

文中关于“两者默认不共享同一浏览器会话，因此更适合作为前后两个阶段协作”的判断，是根据两边官方说明的运行方式做出的工程推断，不是两边文档里的显式一句原话。对实际落地来说，这个推断是保守且合理的默认策略。
