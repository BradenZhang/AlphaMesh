# AlphaMesh

AlphaMesh 是一个多 Agent 投研策略自动化平台的 v0.1 演示初版。当前版本提供可运行的前后端 Dashboard、Mock 行情、LLM Research Agent、策略、回测、风控、Agent Run 日志和 paper trading 闭环；不接真实券商 API，不进行真实交易。

## 能力范围

- FastAPI 后端与 Swagger 文档。
- Market Skill Hub 的 `MockSkillProvider`。
- 多 Agent 投研工作流，默认使用 Mock LLM Provider，包含财报、估值、行业、新闻和投资委员会 Agent。
- `MovingAverageCrossStrategy` 与 `ValuationBandStrategy`。
- 简单回测引擎与指标计算。
- MVP 风控规则与模板化买卖点解释。
- Automation Flow 串联完整流程，并附带 Strategy Review Agent 与 Risk Review Agent 复核。
- Mock Broker Adapter，默认 paper trading，并持久化 paper order。
- PostgreSQL 配置入口，开发环境可使用 SQLite fallback。

## 本地启动

后端:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

前端:

```bash
cd frontend
npm install
npm run dev
```

访问 Swagger:

```text
http://localhost:8000/docs
```

访问前端 Dashboard:

```text
http://localhost:5173
```

健康检查:

```bash
curl http://localhost:8000/api/v1/health
```

## Docker 启动

```bash
docker compose up --build
```

后端服务默认监听:

```text
http://localhost:8000
```

前端服务默认监听:

```text
http://localhost:5173
```

Docker Compose 仅用于本地开发，PostgreSQL 使用本地 trust 认证，不应直接用于生产环境。

## 测试与代码风格

```bash
cd backend
uv run pytest
uv run ruff check .
```

```bash
cd frontend
npm run build
```

## Demo API

查看当前 Agent/LLM provider:

```bash
curl http://localhost:8000/api/v1/agents/status
```

查看最近 Agent Run 日志:

```bash
curl "http://localhost:8000/api/v1/agents/runs?limit=10"
curl "http://localhost:8000/api/v1/agents/llm-calls?limit=10"
```

查看后端可用 LLM Profile:

```bash
curl http://localhost:8000/api/v1/agents/llm-profiles
```

查看当前标的 Memory 上下文:

```bash
curl "http://localhost:8000/api/v1/agents/memory/context?symbol=AAPL&query=低回撤"
```

查看最近 Paper 订单:

```bash
curl "http://localhost:8000/api/v1/orders/paper?limit=10"
```

运行研究 Agent:

```bash
curl -X POST http://localhost:8000/api/v1/research/analyze \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\"}"
```

运行多 Agent 投研工作流:

```bash
curl -X POST http://localhost:8000/api/v1/agents/research/workflow \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\"}"
```

运行 ReAct-lite 工具轨迹:

```bash
curl -X POST http://localhost:8000/api/v1/agents/react/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\",\"max_steps\":3}"
```

写入一条长期偏好记忆:

```bash
curl -X POST http://localhost:8000/api/v1/agents/memory/write \
  -H "Content-Type: application/json" \
  -d "{\"scope\":\"long_term\",\"memory_type\":\"preference\",\"symbol\":\"AAPL\",\"content\":\"偏好低回撤策略和估值安全边际。\",\"importance_score\":0.7}"
curl -X POST http://localhost:8000/api/v1/agents/memory/reload-index
```

手动模式只返回计划，不提交订单:

```bash
curl -X POST http://localhost:8000/api/v1/automation/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"mode\":\"manual\",\"strategy_name\":\"moving_average_cross\"}"
```

Paper 自动模式会提交 mock 订单:

```bash
curl -X POST http://localhost:8000/api/v1/automation/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"mode\":\"paper_auto\",\"strategy_name\":\"moving_average_cross\"}"
```

`live_auto` 默认关闭，会返回明确错误:

```bash
curl -X POST http://localhost:8000/api/v1/automation/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"mode\":\"live_auto\"}"
```

## 安全声明

本项目当前不是生产级交易系统，不接真实资金账户，不调用真实券商 API，不包含任何真实密钥。所有策略信号、回测结果、ReAct 工具轨迹、Memory 摘要和解释仅用于工程框架验证，不构成投资建议。

## LLM Agent 配置

默认 `LLM_PROVIDER=mock`，不需要任何 API key，也不会访问外部模型服务。可在本地 `.env` 中配置 OpenAI-compatible、Anthropic 或 Gemini provider，但真实 key 不应提交到仓库。

```env
LLM_PROVIDER=mock
LLM_MODEL_NAME=mock-research-v1
LLM_BASE_URL=
LLM_API_KEY=
LLM_PROFILES_JSON=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
```

LLM 现在封装在多 Agent 投研和复核层中，输出会被校验成结构化 schema，失败时回退到 deterministic mock 结果。前端只选择后端预设的 `llm_profile_id`，不会持有 API key。LLM 不会绕过风控，也不能触发真实交易；`live_auto` 仍默认关闭。

ReAct-lite 只允许调用行情、K 线、基本面和市场上下文等只读工具。接口返回结构化 `rationale_summary`、`tool_call`、`observation` 和 `final_answer`，不会展示原始 chain-of-thought，也不能调用下单工具。

Memory System 使用本地数据库保存短期记忆和长期记忆，并通过上下文压缩和 Token 预算管理注入 Agent。长期记忆写入时会生成 `content_hash` 和 `token_keywords`，对同一用户、标的和记忆类型做精确/近似去重；服务启动后会预加载长期记忆索引，检索支持中文轻量分词关键词排序。上下文超过 Token 总预算 80% 时会触发 Map-Reduce 压缩：每 5 条旧消息一组做 Map 摘要，多组再 Reduce 合并；只有一组时不再额外 Reduce。所有 LLM 调用会记录 prompt、completion 和 total token 消耗。它只保存结构化摘要、工具轨迹摘要和用户偏好，不保存真实交易凭证或真实资金账户信息。

可选的 OpenAI-compatible profile 示例:

```env
OPENAI_API_KEY=your-local-api-key
LLM_PROFILES_JSON=[{"id":"openai-compatible","label":"OpenAI Compatible","provider":"openai_compatible","model":"gpt-4o-mini","base_url":"https://api.openai.com/v1","api_key_env":"OPENAI_API_KEY"}]
```

### Provider 配置验证

默认 mock provider 验证:

```bash
cd backend
uv run pytest
uv run uvicorn app.main:app --reload
curl http://localhost:8000/api/v1/agents/status
curl -X POST http://localhost:8000/api/v1/research/analyze \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\"}"
curl -X POST http://localhost:8000/api/v1/agents/react/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\"}"
curl "http://localhost:8000/api/v1/agents/memory/stats"
```

说明：在 Python 3.14 环境下，`jieba` 上游会触发 `SyntaxWarning`。项目已在 pytest 配置中过滤该第三方告警，不影响功能和测试结果。

OpenAI-compatible provider 本地验证示例:

```env
LLM_PROVIDER=openai_compatible
LLM_MODEL_NAME=your-model-name
LLM_BASE_URL=https://your-compatible-endpoint/v1
LLM_API_KEY=your-local-api-key
```

配置真实 provider 后，只建议先验证 `/api/v1/agents/llm-profiles`、`/api/v1/research/analyze`、`/api/v1/agents/research/workflow` 和 `/api/v1/agents/react/run`。不要在仓库中提交 `.env`，不要把 LLM 输出直接用于真实交易。
