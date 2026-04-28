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

在 Dashboard 顶部确认:

- Backend 为 `ok / alphamesh`。
- LLM Provider 为 `mock`。
- Market Preview 显示当前标的行情。

API 验证:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/agents/status
curl http://localhost:8000/api/v1/market/quote/AAPL
```

## 3. 运行 Research Agent

在 Dashboard 输入 `AAPL`，点击 `Run Research`。

预期结果:

- 研究报告区域显示 summary、key metrics、估值观点和风险提示。
- Agent Run 日志出现一条 `research` 记录。

API:

```bash
curl -X POST http://localhost:8000/api/v1/research/analyze \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\"}"
```

## 4. 运行 Manual Plan

选择策略:

- `Moving Average Cross`
- 或 `Valuation Band`

点击 `Manual Plan`。

预期结果:

- Automation Flow 展示策略信号、回测摘要、风控结论和解释。
- 不会生成订单。
- Agent Run 日志出现 `automation` 记录。

## 5. 运行 Paper Auto

点击 `Paper Auto`。

预期结果:

- 风控通过时生成 mock paper order。
- 最近 Paper 订单区域显示 order id、symbol、side、status 和金额。
- `/api/v1/orders/paper` 可查询到同一笔订单。

API:

```bash
curl -X POST http://localhost:8000/api/v1/automation/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"mode\":\"paper_auto\",\"strategy_name\":\"moving_average_cross\"}"

curl "http://localhost:8000/api/v1/orders/paper?limit=10"
```

## 6. 安全边界说明

演示结尾需要明确:

- 行情、研究、策略和订单均为 mock/paper。
- `live_auto` 默认关闭。
- LLM 不能绕过 `RiskGuard`。
- 当前结果不构成投资建议。
