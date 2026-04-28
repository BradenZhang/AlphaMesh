# LLM Agents

AlphaMesh 的 LLM Agent MVP 使用一层 LLM Gateway 隔离 LangChain 和业务模块。默认配置为 `LLM_PROVIDER=mock`，因此没有 API key、没有外网时也可以运行测试和 demo。

## Provider

- `mock`: 默认 provider，返回确定性的结构化研究报告。
- `openai` / `openai_compatible`: 适配 OpenAI、DeepSeek、Qwen 等兼容 Chat Completions 的模型。
- `anthropic`: 适配 Anthropic Claude。
- `gemini`: 适配 Google Gemini。

## 配置

真实模型只应在本地 `.env` 中配置:

```env
LLM_PROVIDER=mock
LLM_MODEL_NAME=mock-research-v1
LLM_BASE_URL=
LLM_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
```

不要提交真实 API key。

## 当前 Agent 范围

第一阶段只实现 `LLMResearchAgent`，输入 `symbol`，输出结构化 `ResearchReport`。Agent 可以读取只读 market context，但不能调用下单工具。

Automation Flow 仍按以下顺序执行:

```text
market data -> research -> strategy -> backtest -> risk -> explanation -> paper order
```

LLM 不能绕过风控，`live_auto` 默认关闭。

## 输出防护

LLM 返回内容会经过 `LLMOutputGuard`:

- 支持提取纯 JSON 或 Markdown fenced JSON。
- 使用 Pydantic 校验 `ResearchReport`。
- 拒绝空 `summary`、空 `valuation_view`、空 `risks`。
- 研究 Agent 在输出校验失败时 fallback 到本地 `MockResearchAgent`。
- 真实 provider 调用失败不会被静默吞掉，应由调用方看到明确错误。

## Agent Run 日志

每次 research agent 和 automation flow 运行都会写入 `agent_runs` 表，记录:

- run type 和 status。
- symbol、provider、model。
- 输入摘要和结构化输出摘要。
- 错误信息和耗时。

查看最近运行:

```bash
curl "http://localhost:8000/api/v1/agents/runs?limit=10"
```

## Provider 配置验证

Mock provider 不需要任何 key:

```bash
curl http://localhost:8000/api/v1/agents/status
curl -X POST http://localhost:8000/api/v1/research/analyze \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\"}"
```

OpenAI-compatible provider 示例:

```env
LLM_PROVIDER=openai_compatible
LLM_MODEL_NAME=your-model-name
LLM_BASE_URL=https://your-compatible-endpoint/v1
LLM_API_KEY=your-local-api-key
```

Anthropic provider 示例:

```env
LLM_PROVIDER=anthropic
LLM_MODEL_NAME=claude-your-model
ANTHROPIC_API_KEY=your-local-api-key
```

Gemini provider 示例:

```env
LLM_PROVIDER=gemini
LLM_MODEL_NAME=gemini-your-model
GEMINI_API_KEY=your-local-api-key
```

真实 provider 首次接入时只验证 `/agents/status` 和 `/research/analyze`，不要接入真实交易路径。
