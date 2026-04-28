# AlphaMesh

> 多 Agent 投研策略自动化平台（v0.1 Demo）

AlphaMesh 提供可运行的前后端 Dashboard，覆盖 **行情 -> 投研 -> 策略 -> 回测 -> 风控 -> 解释 -> paper trading** 的完整演示闭环。  
当前版本聚焦工程验证：**不接真实券商 API，不进行真实交易**。

## 目录

- [核心亮点](#核心亮点)
- [快速开始](#快速开始)
- [Docker 启动](#docker-启动)
- [测试与构建](#测试与构建)
- [Demo API 快速清单](#demo-api-快速清单)
- [LLM 与 Agent 配置](#llm-与-agent-配置)
- [安全声明](#安全声明)

## 核心亮点

- FastAPI 后端 + Swagger 文档，React Dashboard 前端。
- `MockSkillProvider` 提供稳定可测的行情/基本面 mock 数据。
- 多 Agent 投研工作流（财报、估值、行业、新闻、投资委员会）。
- ReAct-lite 只读工具链路（结构化 trace，无原始 chain-of-thought）。
- 双策略示例：`MovingAverageCrossStrategy`、`ValuationBandStrategy`。
- 回测指标、RiskGuard 风控、信号解释、Automation Flow 全链路串联。
- Memory System：长期记忆去重、中文轻量检索、Map-Reduce 压缩、Token 预算管理。
- LLM Call 观测：记录每次调用的 `prompt/completion/total tokens`。

## 快速开始

### 1) 启动后端

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### 2) 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 3) 访问地址

- Swagger: `http://localhost:8000/docs`
- Dashboard: `http://localhost:5173`
- Health: `curl http://localhost:8000/api/v1/health`

## Docker 启动

```bash
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

> Docker Compose 仅用于本地开发；PostgreSQL 使用本地 trust 认证，不应直接用于生产环境。

## 测试与构建

后端：

```bash
cd backend
uv run pytest
uv run ruff check .
```

前端：

```bash
cd frontend
npm run build
```

## Demo API 快速清单

### 基础状态

```bash
curl http://localhost:8000/api/v1/agents/status
curl "http://localhost:8000/api/v1/agents/runs?limit=10"
curl "http://localhost:8000/api/v1/agents/llm-calls?limit=10"
curl http://localhost:8000/api/v1/agents/llm-profiles
curl "http://localhost:8000/api/v1/orders/paper?limit=10"
```

### 投研与自动化

```bash
curl -X POST http://localhost:8000/api/v1/research/analyze \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\"}"

curl -X POST http://localhost:8000/api/v1/agents/research/workflow \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\"}"

curl -X POST http://localhost:8000/api/v1/agents/react/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\",\"max_steps\":3}"

curl -X POST http://localhost:8000/api/v1/automation/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"mode\":\"manual\",\"strategy_name\":\"moving_average_cross\"}"

curl -X POST http://localhost:8000/api/v1/automation/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"mode\":\"paper_auto\",\"strategy_name\":\"moving_average_cross\"}"
```

`live_auto` 默认关闭（返回明确错误）：

```bash
curl -X POST http://localhost:8000/api/v1/automation/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"mode\":\"live_auto\"}"
```

### Memory 相关

查看上下文（带中文 query）：

```bash
curl "http://localhost:8000/api/v1/agents/memory/context?symbol=AAPL&query=低回撤"
```

写入长期偏好 + 重载索引：

```bash
curl -X POST http://localhost:8000/api/v1/agents/memory/write \
  -H "Content-Type: application/json" \
  -d "{\"scope\":\"long_term\",\"memory_type\":\"preference\",\"symbol\":\"AAPL\",\"content\":\"偏好低回撤策略和估值安全边际。\",\"importance_score\":0.7}"
curl -X POST http://localhost:8000/api/v1/agents/memory/reload-index
```

## LLM 与 Agent 配置

默认配置使用 Mock，不需要任何 API key：

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

可选 OpenAI-compatible profile 示例：

```env
OPENAI_API_KEY=your-local-api-key
LLM_PROFILES_JSON=[{"id":"openai-compatible","label":"OpenAI Compatible","provider":"openai_compatible","model":"gpt-4o-mini","base_url":"https://api.openai.com/v1","api_key_env":"OPENAI_API_KEY"}]
```

### 运行机制说明

- LLM 输出会做结构化校验，失败自动回退 deterministic mock。
- 前端只传 `llm_profile_id`，不会暴露 API key。
- ReAct-lite 仅允许只读工具（行情/K线/基本面/市场上下文）。
- Memory 系统支持长期记忆去重与中文检索。
- 当上下文超过 Token 总预算 80% 时触发 Map-Reduce 压缩（每 5 条消息一组 Map，单组不做 Reduce）。
- 所有 LLM 调用均记录 token 消耗。

### Provider 配置验证

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

> 在 Python 3.14 环境下，`jieba` 上游会触发 `SyntaxWarning`；项目已在 pytest 配置中过滤该第三方告警，不影响功能和测试结果。

## 安全声明

本项目不是生产级交易系统，不接真实资金账户，不调用真实券商 API，不包含任何真实密钥。  
所有策略信号、回测结果、ReAct 工具轨迹、Memory 摘要和解释仅用于工程框架验证，**不构成投资建议**。  
配置真实 provider 后，建议仅验证 `/api/v1/agents/llm-profiles`、`/api/v1/research/analyze`、`/api/v1/agents/research/workflow`、`/api/v1/agents/react/run`，不要把 LLM 输出直接用于真实交易。
