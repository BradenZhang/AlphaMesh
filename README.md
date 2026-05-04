# AlphaMesh

AlphaMesh 是一个面向股票投研、策略验证和 paper trading 的 AI Agent 工作台。当前版本已经从传统 Dashboard 演进为 **conversation-first 的 AI 股票 Agent Workspace**：用户通过聊天入口发起研究、ReAct 工具调用、自动化计划、组合再平衡和模拟执行，并在消息中查看结构化结果、运行时间线、成本观测和审批状态。

> 重要说明：AlphaMesh 是工程原型和研究工作流系统，不是投资建议系统，也不是生产级券商交易系统。默认路径使用 mock / paper provider，不应直接接入真实资金执行。

## 当前能力概览

- 对话式 Chat Workspace：会话列表、上下文编辑、聊天线程、结构化 artifact、右侧运行面板。
- Chat API：conversation / message 持久化，支持 `chat`、`research`、`manual_plan`、`paper_auto` 四类 reply action。
- ReAct Agent：自然语言问题、只读工具调用、工具 trace、run timeline、按需 Skill 加载、上下文压缩。
- 多 Agent 投研：财报、估值、行业、新闻、投资委员会汇总。
- 自动化工作流：行情、K 线、基本面、投研、策略、回测、风控、解释、paper order。
- 回测增强：交易成本、slippage、walk-forward、IS/OOS 指标、look-ahead bias guard、validation badge。
- Memory：短期/长期记忆、关键词索引、去重、token budget、压缩、上下文注入。
- Provider 架构：market / execution / account 三层能力拆分，已预留 Longbridge、Futu、Eastmoney、IBKR。
- Longbridge 第一版：CLI transport scaffold，已按官方 CLI 风格使用 `--format json`，待真实账号联调。
- Portfolio / Watchlist：自选列表、持仓摘要、批量研究、组合经理 Agent、再平衡 proposal、mock 执行。
- Investment Case：研究结论、信心、风险、数据来源、决策、订单和 outcome 的结构化沉淀。
- Agent Harness：计划状态、任务图、后台运行、结构化审批 FSM。
- LLM 观测：provider、model、tokens、latency、estimated cost。

## 项目结构

```text
backend/
  app/
    api/v1/endpoints/       FastAPI 路由
    core/                   配置、异常、安全开关
    db/                     SQLAlchemy model、session、初始化
    domain/                 枚举和领域模型
    schemas/                Pydantic 请求/响应契约
    services/
      agents/               ReAct、多 Agent runtime、tool registry、Skill loader
      automation/           自动化交易计划、checkpoint、retry/replay
      backtest/             回测、成本、bias guard
      broker/               mock / longbridge / futu / ibkr broker adapter
      case/                 Investment Case 存储
      chat/                 Chat conversation 编排
      connectors/           provider connector 层
      harness/              plan、task、background run、approval FSM
      llm/                  LLM provider、scheduler、pricing、call logger
      market/               market provider 工厂和实现
      memory/               记忆、索引、压缩、token budget
      portfolio/            watchlist、holdings、portfolio、rebalance
      risk/                 风控规则
      strategy/             策略实现
    tests/                  pytest 测试

frontend/
  src/
    components/             Chat workspace、timeline、drawer、portfolio panel
    utils/                  格式化工具
    api.ts                  类型化 API client
    App.tsx                 单页工作台状态编排
    styles.css              全局样式
    types.ts                前端领域类型
```

## 快速启动

### 后端

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### 前端

```powershell
cd frontend
npm install
npm run dev
```

### 访问地址

- 前端工作台：[http://localhost:5173](http://localhost:5173)
- 后端 API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)
- 健康检查：[http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

## Docker Compose

```powershell
docker compose up --build
```

默认服务：

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

当前 Compose 主要用于本地开发。真实 provider、券商 CLI、OpenD、IB Gateway 等本地授权态未必天然在容器内可见，联调时需要额外配置。

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

本轮当前代码已验证：

- `ruff check backend/app`
- 相关后端回归：`34 passed`
- `npm.cmd run build`

## Chat Workspace

前端现在以聊天为主入口，不再是传统多页面 dashboard。

主要交互：

- 左侧：conversation 列表和新建会话。
- 中间：用户消息、助手回复、pending 状态、artifact 展开。
- 右侧：symbol、model profile、strategy、provider、系统状态、LLM cost、cases、portfolio、watchlist。
- 消息 artifact：ReAct trace、research report、multi-agent report、automation result、paper order。

支持的 reply action：

| Action | 说明 |
| --- | --- |
| `chat` | 默认自然语言 ReAct 工具调用 |
| `research` | 多 Agent 投研 |
| `manual_plan` | 自动化流程，但不提交订单 |
| `paper_auto` | 自动化流程，并生成 mock paper order |

## Chat API 示例

创建会话：

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"strategy_name\":\"moving_average_cross\",\"market_provider\":\"mock\"}"
```

发送默认 ReAct 问题：

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Analyze AAPL price action and fundamentals.\",\"action\":\"chat\"}"
```

运行完整投研：

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Run a full research pass.\",\"action\":\"research\"}"
```

运行手动计划：

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Build a manual trading plan.\",\"action\":\"manual_plan\"}"
```

运行 paper automation：

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Run paper automation.\",\"action\":\"paper_auto\"}"
```

## Agent Harness

AlphaMesh 现在内置一层参考 Claude Code harness 思路的 Agent Harness。

### Plan / Todo

ReAct 工具注册表支持：

- `todo_update`：创建或更新当前计划。
- `todo_get`：读取当前计划。
- `load_skill`：按需加载领域 Skill。
- `list_skills`：列出可用 Skill。

`todo_update` 会强制同一时间最多只有一个步骤处于 `in_progress`，避免 agent 同时执行多个互斥步骤。

### Task Graph

任务 API：

```powershell
curl -X POST http://localhost:8000/api/v1/tasks/ `
  -H "Content-Type: application/json" `
  -d "{\"subject\":\"Run AAPL research\",\"owner\":\"research_agent\"}"

curl "http://localhost:8000/api/v1/tasks/?status=pending"
```

任务支持：

- `pending`
- `in_progress`
- `completed`
- `blocked`
- `cancelled`
- `failed`

任务可以通过 `blocked_by` 建立依赖。父任务完成后，依赖它的子任务会自动解除阻塞。

### Background Runs

后台任务目前支持 automation：

```powershell
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/start `
  -H "Content-Type: application/json" `
  -d "{\"run_type\":\"automation\",\"automation_request\":{\"symbol\":\"AAPL\",\"mode\":\"manual\",\"strategy_name\":\"moving_average_cross\"}}"
```

查询后台运行：

```powershell
curl http://localhost:8000/api/v1/tasks/background-runs/{background_run_id}
```

### Approval FSM

审批类型：

- `plan_approval`
- `execution_approval`
- `risk_exception`
- `provider_health_override`

审批状态：

- `pending`
- `approved`
- `rejected`
- `expired`

创建审批：

```powershell
curl -X POST http://localhost:8000/api/v1/approvals/ `
  -H "Content-Type: application/json" `
  -d "{\"request_type\":\"execution_approval\",\"subject\":\"Approve AAPL paper order\",\"requested_by\":\"risk_agent\",\"payload\":{\"symbol\":\"AAPL\",\"side\":\"BUY\"}}"
```

响应审批：

```powershell
curl -X POST http://localhost:8000/api/v1/approvals/{approval_id}/respond `
  -H "Content-Type: application/json" `
  -d "{\"approve\":true,\"reason\":\"Paper-only execution approved.\"}"
```

## Provider 与券商接入

Provider 被拆成三类能力：

- `market_provider`：行情、K 线、基本面、新闻、宏观、情绪。
- `execution_provider`：下单、撤单、订单查询。
- `account_provider`：资金、持仓、账户摘要。

当前预留 provider：

| Provider | Market | Execution | Account | 状态 |
| --- | --- | --- | --- | --- |
| `mock` | 已实现 | 已实现 | 已实现 | 默认可用 |
| `longbridge` | scaffold | scaffold | scaffold | CLI 形态已对齐，待真实联调 |
| `futu` | scaffold | scaffold | scaffold | 预留 OpenD / Skill 接入 |
| `eastmoney` | scaffold | 不支持 | 不支持 | 先定位为只读数据源 |
| `ibkr` | scaffold | scaffold | scaffold | 预留 IBKR API 接入 |

查看 provider health：

```powershell
curl http://localhost:8000/api/v1/agents/providers/health
```

Longbridge CLI 当前按官方 CLI 风格调用，例如：

- `longbridge quote SYMBOL --format json`
- `longbridge kline SYMBOL --period day --start ... --end ... --format json`
- `longbridge order buy|sell SYMBOL QTY --price ... --format json`
- `longbridge portfolio --format json`
- `longbridge positions --format json`

真实联调前需要在本机安装并登录 Longbridge CLI：

```powershell
longbridge auth login
longbridge auth status --format json
longbridge check --format json
```

## 投研、策略、回测、风控

常用接口：

```powershell
curl -X POST http://localhost:8000/api/v1/research/analyze `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\"}"

curl -X POST http://localhost:8000/api/v1/agents/research/workflow `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"market_provider\":\"mock\"}"

curl -X POST http://localhost:8000/api/v1/agents/react/run `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"question\":\"What should I check first?\",\"max_steps\":3}"

curl -X POST http://localhost:8000/api/v1/automation/run `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"mode\":\"manual\",\"strategy_name\":\"moving_average_cross\",\"market_provider\":\"mock\"}"
```

自动化模式：

- `manual`：生成研究、策略、回测、风控、解释，不执行订单。
- `paper_auto`：通过 mock / paper broker 生成模拟订单。
- `live_auto`：接口保留，但默认禁用。

## Portfolio 与 Investment Case

Watchlist：

```powershell
curl http://localhost:8000/api/v1/portfolio/watchlist

curl -X POST http://localhost:8000/api/v1/portfolio/watchlist `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"label\":\"Apple\"}"
```

Portfolio：

```powershell
curl http://localhost:8000/api/v1/portfolio/summary
curl http://localhost:8000/api/v1/portfolio/holdings
```

批量研究和再平衡：

```powershell
curl -X POST http://localhost:8000/api/v1/portfolio/watchlist/research

curl -X POST http://localhost:8000/api/v1/portfolio/rebalance/run `
  -H "Content-Type: application/json" `
  -d "{\"user_id\":\"default\",\"max_orders\":10,\"force\":false}"
```

Investment Case：

```powershell
curl "http://localhost:8000/api/v1/cases?limit=20"
curl http://localhost:8000/api/v1/cases/{case_id}
```

## Memory

查询上下文：

```powershell
curl "http://localhost:8000/api/v1/agents/memory/context?symbol=AAPL&query=valuation"
```

写入长期偏好：

```powershell
curl -X POST http://localhost:8000/api/v1/agents/memory/write `
  -H "Content-Type: application/json" `
  -d "{\"scope\":\"long_term\",\"memory_type\":\"preference\",\"symbol\":\"AAPL\",\"content\":\"Prefer lower drawdown and clear valuation margin of safety.\",\"importance_score\":0.7}"
```

记忆统计和索引：

```powershell
curl http://localhost:8000/api/v1/agents/memory/stats
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

- 前端只传 `llm_profile_id`，API key 保留在后端环境变量中。
- LLM 输出会被解析和校验为结构化 schema。
- ReAct trace 只保存工具调用和 observation，不暴露原始 chain-of-thought。
- LLM 调用会记录 token、latency 和 estimated cost。
- `ModelScheduler` 已预留按任务复杂度选择模型的能力。

## 数据库对象

当前主要持久化表：

- `chat_conversations`
- `chat_messages`
- `agent_runs`
- `llm_calls`
- `agent_memories`
- `run_checkpoints`
- `paper_orders`
- `investment_cases`
- `watchlist_items`
- `portfolio_holdings`
- `agent_plans`
- `agent_tasks`
- `background_runs`
- `approval_requests`

当前项目采用 `Base.metadata.create_all` 和少量 additive column 初始化逻辑，不使用独立 migration 框架。

## 安全边界

- 默认不启用真实资金交易。
- `paper_auto` 仅用于 mock / paper 执行验证。
- 不要提交 API key、券商凭证、`.env`、本地数据库、缓存或日志。
- Longbridge / Futu / IBKR 等真实 provider 联调前必须明确区分 market、account、execution 权限。
- 任何 live execution 都应经过 provider health、risk check、approval FSM 和人工确认。
- 本项目输出不是投资建议，不应直接用于实盘交易。

## 贡献与开发规范

构建命令、测试规范、代码风格和 Git 工作流见 [AGENTS.md](./AGENTS.md)。
