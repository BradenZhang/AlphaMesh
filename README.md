# AlphaMesh

AlphaMesh is an AI stock research and paper-trading automation prototype. It combines a FastAPI backend, a React chat workspace, multi-agent research workflows, ReAct-style tool use, memory, strategy/backtest/risk checks, and paper order simulation.

The current UI is conversation-first: users create chat threads, choose an action mode, send a prompt, and receive assistant replies with expandable structured artifacts such as ReAct traces, multi-agent reports, automation results, and paper orders.

> This project is for engineering validation and research workflow prototyping. It is not a production trading system and does not place real-money trades.

## Features

- FastAPI backend with versioned `/api/v1` routes and Swagger docs.
- React + Vite frontend exposed as an AI agent chat workspace.
- Persistent chat conversations and messages.
- Natural-language `chat` action backed by ReAct runtime.
- Explicit quick actions for `research`, `manual_plan`, and `paper_auto`.
- Multi-agent research workflow with structured committee output.
- Strategy, backtest, risk guard, explanation, and paper order simulation.
- Long-term memory with keyword indexing, deduplication, token budgeting, and compression support.
- LLM provider abstraction with mock, OpenAI-compatible, Anthropic, and Gemini provider paths.
- LLM call logging for token, latency, provider, and model observability.
- Docker Compose local stack with frontend, backend, and PostgreSQL.

## Repository Layout

```text
backend/
  app/
    api/                 FastAPI routers and request validation helpers
    core/                settings and configuration
    db/                  SQLAlchemy base, session, and models
    domain/              enums and domain-level contracts
    schemas/             Pydantic request/response schemas
    services/            agents, automation, LLM, memory, orders, and chat services
    tests/               pytest suite

frontend/
  src/
    components/          chat workspace UI components
    utils/               formatting and UI helpers
    api.ts               typed frontend API client
    App.tsx              workspace state orchestration
    styles.css           app-level styling
    types.ts             frontend domain types
```

## Quick Start

### 1. Start the backend

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### 2. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

### 3. Open the app

- Frontend chat workspace: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

## Docker Compose

Run the full local stack:

```powershell
docker compose up --build
```

Services:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

Docker Compose is configured for local development. PostgreSQL uses local trust authentication and should not be used as-is in production.

## Build And Test

Backend:

```powershell
cd backend
uv run pytest
uv run ruff check .
```

Frontend:

```powershell
cd frontend
npm run build
```

For full-stack changes, run all three checks.

## Chat API

Create a conversation:

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"strategy_name\":\"moving_average_cross\"}"
```

List conversations:

```powershell
curl http://localhost:8000/api/v1/chat/conversations
```

Send a default ReAct-backed chat reply:

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Compare AAPL price action and fundamentals.\"}"
```

Run a multi-agent research reply:

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Run a full research pass.\",\"action\":\"research\"}"
```

Run an automation plan without order submission:

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Build a manual trading plan.\",\"action\":\"manual_plan\"}"
```

Run paper automation:

```powershell
curl -X POST http://localhost:8000/api/v1/chat/conversations/{conversation_id}/reply `
  -H "Content-Type: application/json" `
  -d "{\"message\":\"Run paper automation.\",\"action\":\"paper_auto\"}"
```

Supported reply actions:

- `chat`: natural-language ReAct workflow.
- `research`: full multi-agent research workflow.
- `manual_plan`: automation workflow without paper order submission.
- `paper_auto`: automation workflow with mock paper order submission.

## Legacy And Supporting APIs

Status and observability:

```powershell
curl http://localhost:8000/api/v1/agents/status
curl "http://localhost:8000/api/v1/agents/runs?limit=10"
curl "http://localhost:8000/api/v1/agents/llm-calls?limit=10"
curl http://localhost:8000/api/v1/agents/llm-profiles
curl "http://localhost:8000/api/v1/orders/paper?limit=10"
```

Direct research and automation endpoints:

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

`live_auto` is intentionally disabled by default:

```powershell
curl -X POST http://localhost:8000/api/v1/automation/run `
  -H "Content-Type: application/json" `
  -d "{\"symbol\":\"AAPL\",\"mode\":\"live_auto\"}"
```

## Memory API

Fetch memory context:

```powershell
curl "http://localhost:8000/api/v1/agents/memory/context?symbol=AAPL&query=valuation"
```

Write a long-term memory:

```powershell
curl -X POST http://localhost:8000/api/v1/agents/memory/write `
  -H "Content-Type: application/json" `
  -d "{\"scope\":\"long_term\",\"memory_type\":\"preference\",\"symbol\":\"AAPL\",\"content\":\"Prefer strategies with lower drawdown and clear valuation margin of safety.\",\"importance_score\":0.7}"
```

Reload the in-memory keyword index:

```powershell
curl -X POST http://localhost:8000/api/v1/agents/memory/reload-index
```

## LLM Configuration

The default configuration uses the deterministic mock provider and does not require an API key.

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

OpenAI-compatible profile example:

```env
OPENAI_API_KEY=your-api-key
LLM_PROFILES_JSON=[{"id":"openai-compatible","label":"OpenAI Compatible","provider":"openai_compatible","model":"gpt-4o-mini","base_url":"https://api.openai.com/v1","api_key_env":"OPENAI_API_KEY"}]
```

Notes:

- Frontend requests pass only `llm_profile_id`; API keys remain backend-side.
- LLM outputs are validated into structured schemas. Invalid responses fall back to deterministic mock behavior where applicable.
- ReAct traces store structured tool calls and observations, not raw chain-of-thought.
- LLM calls are logged with provider, model, token counts, and latency.

## Safety

AlphaMesh is not investment advice and not a production brokerage system.

- Real-money execution is not enabled by default.
- Paper orders are mock execution records for workflow validation.
- Do not commit API keys, broker credentials, `.env` files, local databases, or generated caches.
- Do not use LLM-generated signals directly for live trading without independent validation, risk controls, and compliance review.

## Contributor Notes

See `AGENTS.md` for build commands, testing expectations, code style, and Git workflow rules for agents and contributors.
