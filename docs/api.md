# AlphaMesh API

FastAPI 会自动生成 Swagger 文档:

```text
http://localhost:8000/docs
```

## Endpoints

- `GET /api/v1/health`: 服务健康检查。
- `GET /api/v1/market/quote/{symbol}`: 获取 mock 行情快照。
- `GET /api/v1/market/kline/{symbol}`: 获取 mock K 线。
- `POST /api/v1/research/analyze`: 运行 LLM Research Agent，默认使用 Mock LLM Provider。
- `POST /api/v1/strategy/signal`: 生成策略信号。
- `POST /api/v1/backtest/run`: 运行简单回测。
- `POST /api/v1/risk/check`: 执行风控检查。
- `POST /api/v1/automation/run`: 串联完整自动化流程。
- `GET /api/v1/agents/status`: 查看当前 LLM provider 和模型信息。
- `GET /api/v1/agents/runs`: 查看最近 Agent Run 日志。
- `GET /api/v1/orders/paper`: 查看最近 paper order 记录。

## Automation 请求示例

```json
{
  "symbol": "AAPL",
  "mode": "manual",
  "strategy_name": "moving_average_cross"
}
```

`mode` 支持 `manual`、`paper_auto`、`live_auto`。其中 `live_auto` 默认关闭，MVP 不进行真实交易。
