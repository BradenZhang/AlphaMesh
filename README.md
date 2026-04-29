# AlphaMesh

AlphaMesh 是一个 AI 股票投研与 paper trading 自动化原型。项目包含 FastAPI 后端、React 对话式工作台、多 Agent 投研流程、ReAct 工具调用、长期记忆、策略回测、风控检查和模拟纸面订单。

当前版本已经从传统 Dashboard 改为 **conversation-first 的 AI Agent 工作台**：用户可以创建会话，选择执行模式，输入自然语言请求，然后在助手回复中查看可展开的结构化结果，例如 ReAct trace、多 Agent 投研报告、自动化执行结果和 paper order。

> 本项目用于工程验证和投研工作流原型，不是生产级交易系统，不接真实券商账户，也不会执行真实资金交易。

## 核心功能

- FastAPI 后端，统一 `/api/v1` 路由和 Swagger 文档。
- React + Vite 前端，提供 AI 股票 Agent 对话式工作台。
- 持久化 chat conversation 和 chat message。
- 默认 `chat` 模式由 ReAct runtime 处理自然语言问题。
- 快捷动作支持 `research`、`manual_plan`、`paper_auto`。
- 多 Agent 投研流程，输出结构化委员会观点。
- 策略、回测、风控、解释和 paper order 模拟执行链路。
- 长期记忆系统，支持关键词索引、去重、token 预算和压缩。
- LLM Provider 抽象，支持 mock、OpenAI-compatible、Anthropic、Gemini 路径。
- LLM 调用观测，记录 provider、model、token、latency 等信息。
- Docker Compose 本地开发栈，包含 frontend、backend、PostgreSQL。

## 项目结构

```text
backend/
  app/
    api/                 FastAPI 路由和请求校验
    core/                配置和 settings
    db/                  SQLAlchemy base、session、models
    domain/              枚举和领域对象
    schemas/             Pydantic 请求/响应 schema
    services/            agents、automation、LLM、memory、orders、chat 等服务
    tests/               pytest 测试

frontend/
  src/
    components/          chat workspace UI 组件
    utils/               格式化和 UI 辅助函数
    api.ts               类型化前端 API client
    App.tsx              工作台状态编排
    styles.css           全局样式
    types.ts             前端领域类型
```

## 快速开始

### 1. 启动后端

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### 2. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

### 3. 访问地址

- 前端 Chat Workspace: `http://localhost:5173`
- 后端 API 文档: `http://localhost:8000/docs`
- 健康检查: `http://localhost:8000/api/v1/health`

## Docker Compose

启动完整本地开发栈：

```powershell
docker compose up --build
```

服务地址：

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

Docker Compose 仅用于本地开发。当前 PostgreSQL 使用本地 trust 认证，不应直接用于生产环境。

## 构建与测试

后端：

```powershell
cd backend
uv run pytest
uv run ruff check .
```

前端：

```powershell
cd frontend
npm run build
```

如果修改同时涉及前后端或 API 契约，建议三项都运行。

## Chat API

创建会话：

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"strategy_name\":\"moving_average_cross\"}"
```

查看会话列表：

```powershell
curl http://localhost:8000/api/v1/chat/conversations
```

发送默认 ReAct chat 请求：

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Compare AAPL price action and fundamentals.\"}"
```

执行多 Agent 投研：

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Run a full research pass.\",\"action\":\"research\"}"
```

执行手动计划，不提交订单：

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Build a manual trading plan.\",\"action\":\"manual_plan\"}"
```

执行 paper automation：

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Run paper automation.\",\"action\":\"paper_auto\"}"
```

支持的 reply action：

- `chat`：自然语言 ReAct 工具调用流程。
- `research`：完整多 Agent 投研流程。
- `manual_plan`：自动化流程，但不提交 paper order。
- `paper_auto`：自动化流程，并生成模拟 paper order。

## 其他常用 API

状态与观测：

```powershell
curl http://localhost:8000/api/v1/agents/status
curl "http://localhost:8000/api/v1/agents/runs?limit=10"
curl "http://localhost:8000/api/v1/agents/llm-calls?limit=10"
curl http://localhost:8000/api/v1/agents/llm-profiles
curl "http://localhost:8000/api/v1/orders/paper?limit=10"
```

直接调用投研和自动化接口：

```powershell
curl -X POST http://localhost:8000/api/v1/research/analyze `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\"}"

curl -X POST http://localhost:8000/api/v1/agents/research/workflow `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\"}"

curl -X POST http://localhost:8000/api/v1/agents/react/run `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\",\"max_steps\":3}"

curl -X POST http://localhost:8000/api/v1/automation/run `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"mode\":\"manual\",\"strategy_name\":\"moving_average_cross\"}"
```

`live_auto` 默认禁用：

```powershell
curl -X POST http://localhost:8000/api/v1/automation/run `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"mode\":\"live_auto\"}"
```

## Memory API

获取记忆上下文：

```powershell
curl "http://localhost:8000/api/v1/agents/memory/context?symbol=AAPL&query=valuation"
```

写入长期记忆：

```powershell
curl -X POST http://localhost:8000/api/v1/agents/memory/write `
  -H "Content-Type: application/json" `
  -d "{\"scope\":\"long_term\",\"memory_type\":\"preference\",\"symbol\":\"AAPL\",\"content\":\"Prefer strategies with lower drawdown and clear valuation margin of safety.\",\"importance_score\":0.7}"
```

重载内存关键词索引：

```powershell
curl -X POST http://localhost:8000/api/v1/agents/memory/reload-index
```

## LLM 配置

默认使用 deterministic mock provider，不需要 API key。

```env
LLM_PROVIDER=mock
LLM_MODEL_NAME=mock-research-v1
LLM_BASE_URL=
LLM_API_KEY=
LLM_PROFILES_JSON=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3
```

OpenAI-compatible profile 示例：

```env
OPENAI_API_KEY=your-api-key
LLM_PROFILES_JSON=[{"id":"openai-compatible","label":"OpenAI Compatible","provider":"openai_compatible","model":"gpt-4o-mini","base_url":"https://api.openai.com/v1","api_key_env":"OPENAI_API_KEY"}]
```

说明：

- 前端只传 `llm_profile_id`，API key 保留在后端。
- LLM 输出会被校验为结构化 schema；必要时回退到 deterministic mock 行为。
- ReAct trace 只保存结构化 tool call 和 observation，不暴露原始 chain-of-thought。
- LLM call 会记录 provider、model、token 数和 latency。

## 安全说明

AlphaMesh 不是投资建议系统，也不是生产级券商交易系统。

- 默认不启用真实资金执行。
- paper order 只是用于工作流验证的模拟订单。
- 不要提交 API key、券商凭证、`.env` 文件、本地数据库或生成缓存。
- 不要在缺少独立验证、风控和合规审查的情况下，把 LLM 生成的信号直接用于实盘交易。

## 贡献者说明

构建命令、测试规范、代码风格和 Git 工作流请参考 `AGENTS.md`。
