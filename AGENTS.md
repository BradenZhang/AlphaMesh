# AGENTS.md

Guidance for agents and contributors working in this repository.

## Project Layout

- `backend/`: FastAPI backend, SQLAlchemy models, domain services, schemas, and pytest tests.
- `frontend/`: Vite + React + TypeScript frontend.
- `docker-compose.yml`: Local development stack for frontend, backend, and PostgreSQL.

## Build And Run Commands

Backend local development:

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Frontend local development:

```powershell
cd frontend
npm install
npm run dev
```

Docker Compose local stack:

```powershell
docker compose up --build
```

Useful local URLs:

- Frontend: `http://localhost:5173`
- Backend API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

Production-style frontend build check:

```powershell
cd frontend
npm run build
```

## Test And Quality Rules

Backend tests:

```powershell
cd backend
uv run pytest
```

Backend lint:

```powershell
cd backend
uv run ruff check .
```

Frontend build/type check:

```powershell
cd frontend
npm run build
```

Before handing off code changes, run the checks that match the changed surface:

- Backend-only changes: `uv run pytest` and `uv run ruff check .` from `backend/`.
- Frontend-only changes: `npm run build` from `frontend/`.
- API contract or full-stack changes: run both backend tests and frontend build.
- Docker or environment changes: validate `docker compose up --build` when practical.

Test expectations:

- Add or update backend tests under `backend/app/tests/` for new endpoints, workflow behavior, persistence changes, and error handling.
- Keep tests deterministic. Default to mock/local providers unless a test explicitly validates configuration behavior.
- Do not require real broker credentials, live trading, or external paid data services in tests.
- For frontend changes, the current required gate is `npm run build`. Add component or interaction tests only if the project introduces a frontend test runner.

## Code Style

General:

- Keep changes scoped to the requested behavior.
- Prefer existing module boundaries and naming patterns over introducing new architecture.
- Use structured models, schemas, and typed APIs instead of ad hoc dictionaries or string parsing.
- Keep comments short and only where they clarify non-obvious logic.
- Do not commit generated caches, local databases, logs, build output, or environment files.

Backend:

- Python target is `>=3.11`.
- Use FastAPI routers under `backend/app/api/v1/endpoints/`.
- Use Pydantic schemas under `backend/app/schemas/` for request and response contracts.
- Put business logic in services or domain modules, not directly in endpoint handlers.
- Use SQLAlchemy models in `backend/app/db/models.py` for persisted records.
- Follow Ruff settings in `backend/pyproject.toml`: line length `100`, target `py311`, lint groups `E`, `F`, `I`, `UP`, `B`.
- Keep LLM output and tool traces structured. Do not expose raw chain-of-thought.
- Keep live trading disabled by default. Any real execution path must require explicit configuration and tests around safety checks.

Frontend:

- Use React + TypeScript with explicit domain types in `frontend/src/types.ts`.
- Keep API calls in `frontend/src/api.ts`; components should not assemble raw endpoint URLs directly.
- Keep the chat workspace interaction model conversation-first. Avoid reintroducing broad dashboard view switching unless there is a clear product reason.
- Prefer resource-scoped loading and error state over one global loading flag.
- Keep UI dense, readable, and workflow-oriented. Avoid marketing-style hero sections for this app.
- Ensure text does not overflow controls on desktop or mobile breakpoints.
- Do not add new dependencies unless they clearly reduce complexity or match an existing project direction.

## Git Workflow

- Work from a feature branch. Use the `codex/` prefix for Codex-created branches unless the user requests another name.
- Check `git status --short` before editing and before final handoff.
- Never revert user changes or unrelated dirty files.
- Keep commits focused: one coherent behavior or refactor per commit.
- Use clear commit messages, for example:
  - `feat: add chat conversation persistence`
  - `fix: preserve reply state on chat errors`
  - `docs: add contributor agent guide`
- Do not commit secrets, `.env` files, local SQLite databases, logs, caches, `frontend/dist/`, `node_modules/`, or Python virtual environments.
- If a change requires database schema updates, prefer additive changes unless a destructive migration is explicitly requested.
- Before opening a PR or handing off a branch, include:
  - What changed
  - Which checks were run
  - Any known gaps or follow-up work

## Safety Notes

- This project is not a production trading system.
- Do not wire LLM output directly to real-money execution.
- Keep paper trading and mock providers as the default path for local development.
- Treat API keys, broker credentials, and private data as secrets. They must stay out of source control and logs.
