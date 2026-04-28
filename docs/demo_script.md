# AlphaMesh v0.1 Demo Script

这份脚本用于 5 分钟演示 AlphaMesh v0.1 的完整 paper trading 闭环。当前演示只使用 Mock 行情和 Mock LLM Provider，不接真实券商 API，不进行真实交易。

## 1. 启动服务

```bash
docker compose up --build -d
```

打开:

```text
http://localhost:5173
```

Swagger:

```text
http://localhost:8000/docs
```

## 2. 检查系统状态

在 Dashboard 左侧和工作台顶部确认:

- Backend 为 `ok / alphamesh`。
- LLM Profile 区域显示 `Mock LLM`，也可看到后端预设的 OpenAI-compatible profile。
- Market Preview 显示当前标的行情。

API 验证:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/agents/status
curl http://localhost:8000/api/v1/agents/llm-profiles
curl http://localhost:8000/api/v1/market/quote/AAPL
```

## 3. 运行 Research Agent

在 Dashboard 输入 `AAPL`，选择 `Mock LLM` profile，点击 `Run Research`。

预期结果:

- Multi-Agent Research 区域显示财报、估值、行业、新闻四类 finding 和委员会结论。
- 研究报告区域显示由委员会结论转换出的 summary、key metrics、估值观点和风险提示。
- Agent Run 日志出现各子 Agent、`investment_committee_agent` 和聚合 `research` 记录。

API:

```bash
curl -X POST http://localhost:8000/api/v1/research/analyze \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\"}"

curl -X POST http://localhost:8000/api/v1/agents/research/workflow \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\"}"
```

## 4. 运行 Manual Plan

点击 `Run ReAct`。

预期结果:

- ReAct Trace 区域展示只读工具调用步骤。
- 每一步包含 rationale summary、action 和 observation。
- Agent Run 日志出现 `react_agent` 记录。

API:

```bash
curl -X POST http://localhost:8000/api/v1/agents/react/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\",\"max_steps\":3}"

curl "http://localhost:8000/api/v1/agents/memory/context?symbol=AAPL"
```

## 5. 查看 Memory System

预期结果:

- Memory 面板显示短期记忆、长期记忆和 token 预算。
- 运行 Research 或 ReAct 后，最近记忆会出现 `research_summary` 或 `react_trace`。
- 点击 `Compact` 会把当前标的上下文压缩成长期摘要。

API:

```bash
curl "http://localhost:8000/api/v1/agents/memory/stats"
curl "http://localhost:8000/api/v1/agents/memory/recent?limit=10"
curl -X POST "http://localhost:8000/api/v1/agents/memory/compact?symbol=AAPL"
```

## 6. 运行 Manual Plan

选择策略:

- `Moving Average Cross`
- 或 `Valuation Band`

点击 `Manual Plan`。

预期结果:

- Automation Flow 展示策略信号、回测摘要、策略复核、风控复核和解释。
- 不会生成订单。
- Agent Run 日志出现 `automation` 记录。

## 7. 运行 Paper Auto

点击 `Paper Auto`。

预期结果:

- 风控通过时生成 mock paper order。
- 最近 Paper 订单区域显示 order id、symbol、side、status 和金额。
- `/api/v1/orders/paper` 可查询到同一笔订单。

API:

```bash
curl -X POST http://localhost:8000/api/v1/automation/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"mode\":\"paper_auto\",\"strategy_name\":\"moving_average_cross\",\"llm_profile_id\":\"mock\"}"

curl "http://localhost:8000/api/v1/orders/paper?limit=10"
```

## 8. 安全边界说明

演示结尾需要明确:

- 行情、研究、策略和订单均为 mock/paper。
- `live_auto` 默认关闭。
- LLM 不能绕过 `RiskGuard`。
- 前端只选择后端 LLM Profile，不保存或发送真实 API key。
- ReAct 只展示结构化工具轨迹，不展示原始 chain-of-thought。
- Memory 只保存结构化摘要和偏好，不保存真实密钥、真实账户或真实交易指令。
- Strategy Review 和 Risk Review 只做辅助复核，不能直接下单。
- 当前结果不构成投资建议。
