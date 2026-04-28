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
LLM_PROFILES_JSON=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
```

不要提交真实 API key。

## LLM Profile 切换

前端模型切换使用后端预设的 LLM Profile。Profile 只暴露 `id`、`label`、`provider`、`model` 和配置状态，不返回 API key。

查看可用 Profile:

```bash
curl http://localhost:8000/api/v1/agents/llm-profiles
```

OpenAI-compatible profile 示例:

```env
OPENAI_API_KEY=your-local-api-key
LLM_PROFILES_JSON=[{"id":"openai-compatible","label":"OpenAI Compatible","provider":"openai_compatible","model":"gpt-4o-mini","base_url":"https://api.openai.com/v1","api_key_env":"OPENAI_API_KEY"}]
```

请求时可传入 `llm_profile_id`:

```bash
curl -X POST http://localhost:8000/api/v1/agents/research/workflow \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\"}"
```

## 当前 Agent 范围

当前实现包含一个完整演示闭环:

- `Financial Statement Agent`: 财务质量和关键指标观察。
- `Valuation Agent`: 估值区间和相对吸引力判断。
- `Industry Agent`: 行业需求和竞争环境判断。
- `News Agent`: 新闻和情绪风险判断。
- `Investment Committee Agent`: 汇总四类 finding，生成委员会结论。
- `Strategy Review Agent`: 复核策略信号与回测是否匹配。
- `Risk Review Agent`: 复核 `RiskGuard` 结果，但不能替代风控。
- `ReAct-lite Agent`: 独立演示只读工具调用轨迹，展示 action 和 observation。

`LLMResearchAgent` 默认调用 `MultiAgentResearchWorkflow`，并转换为兼容既有策略链路的 `ResearchReport`。Agent 可以读取只读 market context，但不能调用下单工具。

Automation Flow 仍按以下顺序执行:

```text
market data -> multi-agent research -> strategy -> backtest -> strategy review -> risk -> risk review -> explanation -> paper order
```

LLM 不能绕过风控，`live_auto` 默认关闭。

## ReAct-lite

ReAct-lite 用于演示 Agent 如何选择只读工具、获取 observation 并形成摘要。系统不会展示原始 chain-of-thought，只返回结构化字段:

- `rationale_summary`
- `tool_call`
- `observation`
- `final_answer`

可用工具白名单:

- `get_quote`
- `get_kline`
- `get_fundamentals`
- `get_market_context`

示例:

```bash
curl -X POST http://localhost:8000/api/v1/agents/react/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\",\"max_steps\":3}"
```

ReAct-lite 不允许调用下单工具，未知工具会被结构化拒绝。

## Memory System

Memory System 为 Agent 注入受控上下文，分为四部分:

- `ShortTermMemory`: 保存最近 research、ReAct trace、automation 摘要，默认有 TTL。
- `LongTermMemory`: 保存用户偏好、关键投研摘要和重要风险，写入时自动去重并持久化。
- `MemoryIndex`: 服务启动时加载长期记忆，写入后同步更新，按中文关键词、重要性和时间排序召回。
- `tokenizer`: 优先使用 `jieba`，缺失时回退到内置中文 2-3 字滑窗和英文/数字分词。
- `ContextCompressor`: 当上下文超过预算阈值时，使用 Map-Reduce 将旧消息压缩成简短上下文。
- `TokenBudgetManager`: 用简单 token 估算做预算分配，超过总预算 80% 时触发压缩，避免 prompt 膨胀。
- `LLMCallLogger`: 记录每次 LLM 调用的 prompt、completion 和 total token 消耗。

查看当前标的记忆上下文:

```bash
curl "http://localhost:8000/api/v1/agents/memory/context?symbol=AAPL&query=低回撤"
```

手动写入长期偏好:

```bash
curl -X POST http://localhost:8000/api/v1/agents/memory/write \
  -H "Content-Type: application/json" \
  -d "{\"scope\":\"long_term\",\"memory_type\":\"preference\",\"symbol\":\"AAPL\",\"content\":\"偏好低回撤策略和估值安全边际。\",\"importance_score\":0.7}"
```

长期记忆响应会返回 `content_hash` 和 `token_keywords`。当精确重复或高度相似内容命中旧记录时，不新增重复记录，而是更新旧记录的重要性、metadata 和时间戳，并标记 `deduplicated`。Memory 不保存真实密钥、真实账户或真实交易指令，也不展示原始 chain-of-thought。

Map-Reduce 压缩流程:

- Map 阶段把旧消息按每 5 条一组切分，每组独立调用 LLM 生成分片摘要。
- Reduce 阶段把多个分片摘要合并成最终摘要。
- 如果只有一个分片，直接使用该 Map 摘要，不再额外调用一次 Reduce。
- 每次 Map/Reduce LLM 调用都会写入 `llm_calls`，可通过 `GET /api/v1/agents/llm-calls` 查看 token 消耗。

## 输出防护

LLM 返回内容会经过 `LLMOutputGuard`:

- 支持提取纯 JSON 或 Markdown fenced JSON。
- 使用 Pydantic 校验 `ResearchReport`、`AgentFinding`、`InvestmentCommitteeReport`、`StrategyReviewReport` 和 `RiskReviewReport`。
- 拒绝空 `summary`、空 `valuation_view`、空 `risks`。
- 多 Agent 子任务在输出校验失败时 fallback 到 deterministic mock 结果，并记录 `fallback` 状态。
- 真实 provider 调用失败不会被静默吞掉，应由调用方看到明确错误。

## Agent Run 日志

每次多 Agent 子任务、聚合 research 和 automation flow 运行都会写入 `agent_runs` 表，记录:

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
curl http://localhost:8000/api/v1/agents/llm-profiles
curl -X POST http://localhost:8000/api/v1/research/analyze \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\"}"
curl -X POST http://localhost:8000/api/v1/agents/research/workflow \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\"}"
curl -X POST http://localhost:8000/api/v1/agents/react/run \
  -H "Content-Type: application/json" \
  -d "{\"symbol\":\"AAPL\",\"llm_profile_id\":\"mock\"}"
curl "http://localhost:8000/api/v1/agents/memory/context?symbol=AAPL"
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

真实 provider 首次接入时只验证 `/agents/status`、`/agents/llm-profiles`、`/research/analyze` 和 `/agents/research/workflow`，不要接入真实交易路径。
