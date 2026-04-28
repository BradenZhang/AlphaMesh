# AlphaMesh API

FastAPI 会自动生成 Swagger 文档:

```text
http://localhost:8000/docs
```

## Endpoints

- `GET /api/v1/health`: 服务健康检查。
- `GET /api/v1/market/quote/{symbol}`: 获取 mock 行情快照。
- `GET /api/v1/market/kline/{symbol}`: 获取 mock K 线。
- `POST /api/v1/research/analyze`: 运行 LLM Research Agent，默认由多 Agent workflow 转换为兼容的 `ResearchReport`。
- `POST /api/v1/strategy/signal`: 生成策略信号。
- `POST /api/v1/backtest/run`: 运行简单回测。
- `POST /api/v1/risk/check`: 执行风控检查。
- `POST /api/v1/automation/run`: 串联完整自动化流程。
- `GET /api/v1/agents/status`: 查看当前 LLM provider 和模型信息。
- `GET /api/v1/agents/llm-profiles`: 查看后端预设的安全 LLM Profile 列表。
- `GET /api/v1/agents/runs`: 查看最近 Agent Run 日志。
- `GET /api/v1/agents/llm-calls`: 查看最近 LLM 调用 token 消耗。
- `POST /api/v1/agents/react/run`: 运行 ReAct-lite 只读工具调用轨迹。
- `GET /api/v1/agents/memory/context`: 获取当前标的可注入的压缩记忆上下文，支持可选 `query`。
- `GET /api/v1/agents/memory/recent`: 查看最近记忆。
- `POST /api/v1/agents/memory/write`: 手动写入记忆。
- `POST /api/v1/agents/memory/compact`: 手动压缩当前标的记忆为长期摘要。
- `GET /api/v1/agents/memory/stats`: 查看短期/长期记忆统计和长期索引状态。
- `POST /api/v1/agents/memory/reload-index`: 手动从数据库重载长期记忆索引。
- `POST /api/v1/agents/research/workflow`: 运行完整多 Agent 投研工作流，返回 findings、委员会报告和兼容研报。
- `GET /api/v1/orders/paper`: 查看最近 paper order 记录。

## Automation 请求示例

```json
{
  "symbol": "AAPL",
  "mode": "manual",
  "strategy_name": "moving_average_cross",
  "llm_profile_id": "mock"
}
```

`mode` 支持 `manual`、`paper_auto`、`live_auto`。其中 `live_auto` 默认关闭，MVP 不进行真实交易。

Automation 响应会保留既有字段，并额外返回 `multi_agent_report` 和 `agent_reviews`。这些字段用于解释和展示，不改变 `RiskGuard` 对 paper 自动执行的最终约束。

`llm_profile_id` 可选。未传时使用后端 `.env` 默认 provider；传入时仅影响多 Agent 投研和复核，不影响风控规则或下单权限。

## ReAct 请求示例

```json
{
  "symbol": "AAPL",
  "llm_profile_id": "mock",
  "max_steps": 3
}
```

ReAct-lite 只允许调用只读工具，例如行情、K 线、基本面和市场上下文。响应中的 trace 是结构化工具轨迹，不包含原始 chain-of-thought，也不会触发下单。

## Memory 请求示例

```json
{
  "scope": "long_term",
  "memory_type": "preference",
  "symbol": "AAPL",
  "content": "偏好低回撤策略和估值安全边际。",
  "importance_score": 0.7
}
```

查询中文长期记忆上下文:

```bash
curl "http://localhost:8000/api/v1/agents/memory/context?symbol=AAPL&query=低回撤"
```

长期记忆写入会自动生成 `content_hash` 和 `token_keywords`。同一用户、标的和记忆类型下，精确重复内容不会新增记录；关键词高度相似的内容会更新旧记录并在 metadata 中标记 `deduplicated`。Memory System 用于增强 Agent 上下文。短期记忆默认用于最近运行摘要和 ReAct trace，长期记忆用于偏好、关键结论和压缩摘要。Memory 不保存真实密钥、真实账户或真实交易指令。

当记忆上下文 token 估算超过总预算 80% 时，`memory/context` 会触发 Map-Reduce 压缩，并在响应中返回 `compression_triggered`、`compression_strategy`、`budget_allocation` 和 `compression_token_usage`。Map 阶段每 5 条旧消息一组调用 LLM 生成分片摘要；Reduce 阶段合并多个分片摘要；只有一个分片时直接使用 Map 摘要，不额外调用 Reduce。

LLM token 消耗查询:

```bash
curl "http://localhost:8000/api/v1/agents/llm-calls?limit=10"
```

测试补充：Python 3.14 下 `jieba` 可能输出上游 `SyntaxWarning`，已在 pytest 配置中过滤，接口与功能不受影响。
