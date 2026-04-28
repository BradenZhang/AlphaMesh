import { useEffect, useMemo, useState } from "react";
import {
  compactMemory,
  fetchAgentRuns,
  fetchAgentStatus,
  fetchHealth,
  fetchLLMProfiles,
  fetchMemoryContext,
  fetchMemoryStats,
  fetchPaperOrders,
  fetchQuote,
  fetchRecentMemories,
  reloadMemoryIndex,
  runAutomation,
  runMultiAgentResearch,
  runReActAgent
} from "./api";
import type {
  AgentRun,
  AgentStatus,
  AutomationResult,
  LLMProfile,
  LLMProfileListResponse,
  MemoryContext,
  MemoryRecord,
  MemoryStats,
  MultiAgentResearchReport,
  PaperOrder,
  Quote,
  ReActResult,
  ResearchReport,
  StrategyName
} from "./types";

type LoadState = "idle" | "loading" | "success" | "error";

function formatPct(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

function formatMoney(value: number): string {
  return new Intl.NumberFormat("en-US", {
    currency: "USD",
    maximumFractionDigits: 2,
    style: "currency"
  }).format(value);
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    month: "2-digit",
    day: "2-digit"
  }).format(new Date(value));
}

function badgeClass(value: string): string {
  return `badge ${value.toLowerCase().replaceAll("_", "-")}`;
}

export default function App() {
  const [symbol, setSymbol] = useState("AAPL");
  const [health, setHealth] = useState<string>("checking");
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [llmProfiles, setLLMProfiles] = useState<LLMProfileListResponse | null>(null);
  const [selectedLLMProfileId, setSelectedLLMProfileId] = useState<string | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [orders, setOrders] = useState<PaperOrder[]>([]);
  const [memoryContext, setMemoryContext] = useState<MemoryContext | null>(null);
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
  const [memoryQuery, setMemoryQuery] = useState("");
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [strategyName, setStrategyName] = useState<StrategyName>("moving_average_cross");
  const [research, setResearch] = useState<ResearchReport | null>(null);
  const [multiAgentReport, setMultiAgentReport] = useState<MultiAgentResearchReport | null>(null);
  const [automation, setAutomation] = useState<AutomationResult | null>(null);
  const [reactResult, setReActResult] = useState<ReActResult | null>(null);
  const [state, setState] = useState<LoadState>("idle");
  const [error, setError] = useState<string | null>(null);

  const normalizedSymbol = useMemo(() => symbol.trim().toUpperCase() || "AAPL", [symbol]);
  const isLoading = state === "loading";
  const activeLLMProfileId = selectedLLMProfileId ?? llmProfiles?.default_profile_id ?? null;
  const activeLLMProfile =
    llmProfiles?.profiles.find((profile) => profile.id === activeLLMProfileId) ?? null;

  async function refreshStatus() {
    const [
      healthPayload,
      statusPayload,
      profilePayload,
      runPayload,
      orderPayload,
      quotePayload,
      memoryContextPayload,
      memoryStatsPayload,
      memoryPayload
    ] = await Promise.all([
        fetchHealth(),
        fetchAgentStatus(),
        fetchLLMProfiles(),
        fetchAgentRuns(),
        fetchPaperOrders(),
        fetchQuote(normalizedSymbol),
        fetchMemoryContext(normalizedSymbol, memoryQuery),
        fetchMemoryStats(),
        fetchRecentMemories()
      ]);
    setHealth(`${healthPayload.status} / ${healthPayload.service}`);
    setAgentStatus(statusPayload);
    setLLMProfiles(profilePayload);
    setSelectedLLMProfileId((current) => current ?? profilePayload.default_profile_id);
    setRuns(runPayload);
    setOrders(orderPayload);
    setQuote(quotePayload);
    setMemoryContext(memoryContextPayload);
    setMemoryStats(memoryStatsPayload);
    setMemories(memoryPayload);
  }

  useEffect(() => {
    refreshStatus().catch((err: unknown) => {
      setHealth("unavailable");
      setError(err instanceof Error ? err.message : "Failed to load backend status.");
    });
  }, []);

  async function handleResearch() {
    setState("loading");
    setError(null);
    try {
      const report = await runMultiAgentResearch(normalizedSymbol, activeLLMProfileId);
      setMultiAgentReport(report);
      setResearch(report.research_report);
      setState("success");
      await refreshStatus();
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Research request failed.");
    }
  }

  async function handleAutomation(mode: "manual" | "paper_auto") {
    setState("loading");
    setError(null);
    try {
      const result = await runAutomation(normalizedSymbol, mode, strategyName, activeLLMProfileId);
      setAutomation(result);
      setResearch(result.research_report);
      setMultiAgentReport(result.multi_agent_report);
      setState("success");
      await refreshStatus();
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Automation request failed.");
    }
  }

  async function handleReAct() {
    setState("loading");
    setError(null);
    try {
      const result = await runReActAgent(normalizedSymbol, activeLLMProfileId);
      setReActResult(result);
      setState("success");
      await refreshStatus();
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "ReAct request failed.");
    }
  }

  async function handleCompactMemory() {
    setState("loading");
    setError(null);
    try {
      await compactMemory(normalizedSymbol);
      setState("success");
      await refreshStatus();
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Memory compact request failed.");
    }
  }

  async function handleMemorySearch() {
    setState("loading");
    setError(null);
    try {
      const context = await fetchMemoryContext(normalizedSymbol, memoryQuery);
      setMemoryContext(context);
      setState("success");
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Memory search request failed.");
    }
  }

  async function handleReloadMemoryIndex() {
    setState("loading");
    setError(null);
    try {
      const stats = await reloadMemoryIndex();
      setMemoryStats(stats);
      await handleMemorySearch();
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Memory index reload request failed.");
    }
  }

  return (
    <div className="appShell">
      <aside className="sidebar">
        <div className="brandMark">AM</div>
        <div>
          <p className="eyebrow">AlphaMesh Console</p>
          <h1>多 Agent 投研工作台</h1>
          <p className="heroText">
            借鉴 PaiFlow 控制台的模型选择和工作台布局，用后端 LLM Profile 安全切换
            Mock 或 OpenAI-compatible 通道。
          </p>
        </div>
        <nav className="navStack">
          {["Workbench", "Models", "Research", "Automation", "Logs"].map((item) => (
            <span key={item}>{item}</span>
          ))}
        </nav>
        <div className="statusGrid">
          <StatusCard label="Backend" value={health} accent="green" />
          <StatusCard
            label="Env Provider"
            value={agentStatus?.provider ?? "loading"}
            accent={agentStatus?.is_mock ? "blue" : "purple"}
          />
          <StatusCard label="Env Model" value={agentStatus?.model ?? "loading"} accent="slate" />
        </div>
      </aside>

      <main className="workspace">
        <section className="topBar panel">
          <div className="controlIntro">
            <p className="eyebrow">Command Center</p>
            <h2>运行投研流程</h2>
            <p className="muted">选择模型 Profile、标的和策略后，运行多 Agent 投研或完整自动化计划。</p>
          </div>
          <div className="symbolBox">
            <label htmlFor="symbol">Symbol</label>
            <input
              id="symbol"
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              placeholder="AAPL"
            />
            <span>当前标的：{normalizedSymbol}</span>
          </div>
          <div className="symbolBox">
            <label htmlFor="strategy">Strategy</label>
            <select
              id="strategy"
              value={strategyName}
              onChange={(event) => setStrategyName(event.target.value as StrategyName)}
            >
              <option value="moving_average_cross">Moving Average Cross</option>
              <option value="valuation_band">Valuation Band</option>
            </select>
            <span>当前策略：{strategyName}</span>
          </div>
          <div className="buttonGroup">
            <button disabled={isLoading} onClick={handleResearch}>
              {isLoading ? "Running..." : "Run Research"}
            </button>
            <button className="secondary" disabled={isLoading} onClick={handleReAct}>
              Run ReAct
            </button>
            <button className="secondary" disabled={isLoading} onClick={() => handleAutomation("manual")}>
              Manual Plan
            </button>
            <button className="success" disabled={isLoading} onClick={() => handleAutomation("paper_auto")}>
              Paper Auto
            </button>
          </div>
        </section>

        {error ? <div className="alert">请求失败：{error}</div> : null}

        <section className="dashboardGrid">
          <div className="primaryColumn">
            <ModelProfilePanel
              activeProfile={activeLLMProfile}
              profiles={llmProfiles?.profiles ?? []}
              selectedProfileId={activeLLMProfileId}
              onSelect={setSelectedLLMProfileId}
            />
            <MarketPanel quote={quote} />
            <ReActTracePanel result={reactResult} />
            <MultiAgentPanel report={multiAgentReport} />
            <section className="grid">
              <ResearchPanel research={research} />
              <AutomationPanel automation={automation} />
            </section>
          </div>

          <aside className="rightRail">
            <MemoryPanel
              context={memoryContext}
              stats={memoryStats}
              memories={memories}
              query={memoryQuery}
              onQueryChange={setMemoryQuery}
              onSearch={handleMemorySearch}
              onCompact={handleCompactMemory}
              onReloadIndex={handleReloadMemoryIndex}
              isLoading={isLoading}
            />
            <PaperOrdersPanel orders={orders} />
            <AgentRunsPanel runs={runs} onRefresh={refreshStatus} />
          </aside>
        </section>
      </main>
    </div>
  );
}

function ModelProfilePanel({
  activeProfile,
  profiles,
  selectedProfileId,
  onSelect
}: {
  activeProfile: LLMProfile | null;
  profiles: LLMProfile[];
  selectedProfileId: string | null;
  onSelect: (profileId: string) => void;
}) {
  return (
    <section className="panel modelPanel">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Model Profiles</p>
          <h2>大模型切换</h2>
        </div>
        {activeProfile ? <span className={badgeClass(activeProfile.provider)}>{activeProfile.provider}</span> : null}
      </div>
      <p className="muted">
        前端只选择后端预设 Profile；API key、base_url 和真实 provider 配置都保留在后端环境中。
      </p>
      <div className="profileGrid">
        {profiles.length === 0 ? (
          <div className="profileCard active">
            <strong>Loading profiles</strong>
            <span>等待后端 LLM Profile 列表</span>
          </div>
        ) : (
          profiles.map((profile) => (
            <button
              className={`profileCard ${profile.id === selectedProfileId ? "active" : ""}`}
              key={profile.id}
              onClick={() => onSelect(profile.id)}
              type="button"
            >
              <div>
                <strong>{profile.label}</strong>
                <span>{profile.model}</span>
              </div>
              <small>
                {profile.provider}
                {profile.is_default ? " / default" : ""}
                {profile.base_url_configured ? " / base_url" : ""}
                {profile.api_key_configured ? " / key ready" : profile.is_mock ? "" : " / key missing"}
              </small>
            </button>
          ))
        )}
      </div>
    </section>
  );
}

function PaperOrdersPanel({ orders }: { orders: PaperOrder[] }) {
  return (
    <section className="panel railPanel">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Paper Trading</p>
          <h2>最近订单</h2>
        </div>
        <span className="badge hold">{orders.length}</span>
      </div>
      <div className="orderGrid compactList">
        {orders.length === 0 ? (
          <p className="muted">暂无 paper 订单，点击 Paper Auto 后会写入数据库。</p>
        ) : (
          orders.map((order) => (
            <div className="orderCard" key={order.order_id}>
              <div>
                <strong>{order.symbol}</strong>
                <span className={badgeClass(order.side)}>{order.side}</span>
                <span className={badgeClass(order.status)}>{order.status}</span>
              </div>
              <p>{order.order_id}</p>
              <small>
                {order.quantity} @ {order.limit_price ? formatMoney(order.limit_price) : "MKT"} /{" "}
                {order.estimated_amount ? formatMoney(order.estimated_amount) : "n/a"}
              </small>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function MemoryPanel({
  context,
  stats,
  memories,
  query,
  onQueryChange,
  onSearch,
  onCompact,
  onReloadIndex,
  isLoading
}: {
  context: MemoryContext | null;
  stats: MemoryStats | null;
  memories: MemoryRecord[];
  query: string;
  onQueryChange: (query: string) => void;
  onSearch: () => void;
  onCompact: () => void;
  onReloadIndex: () => void;
  isLoading: boolean;
}) {
  const usagePct =
    context && context.token_budget > 0 ? Math.min(context.token_estimate / context.token_budget, 1) : 0;

  return (
    <section className="panel railPanel memoryPanel">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Memory System</p>
          <h2>记忆管理</h2>
        </div>
        <button className="ghost" disabled={isLoading} onClick={onCompact}>
          Compact
        </button>
      </div>
      <div className="memorySearch">
        <input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="中文检索：低回撤、估值安全边际..."
        />
        <button className="ghost" disabled={isLoading} onClick={onSearch}>
          Search
        </button>
        <button className="ghost" disabled={isLoading} onClick={onReloadIndex}>
          Reload
        </button>
      </div>
      <div className="memoryStats">
        <div>
          <span>Short</span>
          <strong>{stats?.short_term_count ?? 0}</strong>
        </div>
        <div>
          <span>Long</span>
          <strong>{stats?.long_term_count ?? 0}</strong>
        </div>
        <div>
          <span>Tokens</span>
          <strong>{stats?.total_token_estimate ?? 0}</strong>
        </div>
        <div>
          <span>Index</span>
          <strong>{stats?.index_loaded_count ?? 0}</strong>
        </div>
        <div>
          <span>Keywords</span>
          <strong>{stats?.index_keyword_count ?? 0}</strong>
        </div>
      </div>
      <div className="budgetBar">
        <span style={{ width: `${usagePct * 100}%` }} />
      </div>
      <small className="muted">
        Context {context?.token_estimate ?? 0} / {context?.token_budget ?? 0} tokens
        {context?.compacted ? " / compacted" : ""}
        {context?.compression_triggered ? ` / ${context.compression_strategy}` : ""}
        {context?.query ? ` / query: ${context.query}` : ""}
      </small>
      {context?.compression_triggered ? (
        <small className="muted">
          Map-Reduce token usage: {context.compression_token_usage.total_tokens ?? 0} / trigger{" "}
          {context.budget_allocation.compression_trigger ?? 0}
        </small>
      ) : null}
      <div className="memoryContext">
        <strong>当前上下文</strong>
        <p>{context?.context ?? "暂无记忆上下文。"}</p>
      </div>
      <div className="memoryList">
        {memories.length === 0 ? (
          <p className="muted">运行 Research、ReAct 或 Automation 后会写入记忆。</p>
        ) : (
          memories.slice(0, 5).map((memory) => (
            <article className="memoryItem" key={memory.memory_id}>
              <div>
                <span className={badgeClass(memory.scope)}>{memory.scope}</span>
                <span className="muted">{memory.memory_type}</span>
                {memory.metadata.deduplicated ? <span className="dedupeBadge">deduped</span> : null}
              </div>
              <p>{memory.content}</p>
              <div className="keywordList">
                {memory.token_keywords.slice(0, 6).map((keyword) => (
                  <span className="keywordChip" key={`${memory.memory_id}-${keyword}`}>
                    {keyword}
                  </span>
                ))}
              </div>
              {memory.content_hash ? (
                <small className="muted">hash {memory.content_hash.slice(0, 10)}</small>
              ) : null}
            </article>
          ))
        )}
      </div>
    </section>
  );
}

function AgentRunsPanel({ runs, onRefresh }: { runs: AgentRun[]; onRefresh: () => void }) {
  return (
    <section className="panel railPanel">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Observability</p>
          <h2>Agent Run 日志</h2>
        </div>
        <button className="ghost" onClick={onRefresh}>
          Refresh
        </button>
      </div>
      <div className="runList">
        {runs.length === 0 ? (
          <p className="muted">暂无运行记录，先执行一次 Research 或 Automation。</p>
        ) : (
          runs.map((run) => (
            <div className="runItem" key={run.run_id}>
              <div>
                <strong>{run.run_type}</strong>
                <span>{run.symbol ?? "-"}</span>
                <span className={badgeClass(run.status)}>{run.status}</span>
              </div>
              <small>
                {formatDateTime(run.created_at)} / {run.provider ?? "n/a"} / {run.latency_ms}ms
              </small>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function StatusCard({
  label,
  value,
  accent
}: {
  label: string;
  value: string;
  accent: "green" | "blue" | "purple" | "slate";
}) {
  return (
    <div className={`statusCard ${accent}`}>
      <div className="statusDot" />
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function MarketPanel({ quote }: { quote: Quote | null }) {
  const change = quote ? quote.price - quote.previous_close : 0;
  const changePct = quote && quote.previous_close ? change / quote.previous_close : 0;

  return (
    <section className="panel marketPanel">
      <div>
        <p className="eyebrow">Market Preview</p>
        <h2>{quote ? quote.symbol : "等待行情"}</h2>
        <p className="muted">Mock 行情用于演示完整投研链路，不代表实时市场数据。</p>
      </div>
      {quote ? (
        <div className="marketMetrics">
          <div>
            <span>Last Price</span>
            <strong>{formatMoney(quote.price)}</strong>
          </div>
          <div>
            <span>Change</span>
            <strong className={change >= 0 ? "positive" : "negative"}>
              {change >= 0 ? "+" : ""}
              {change.toFixed(2)} ({formatPct(changePct)})
            </strong>
          </div>
          <div>
            <span>Range</span>
            <strong>
              {formatMoney(quote.low)} - {formatMoney(quote.high)}
            </strong>
          </div>
          <div>
            <span>Volume / Provider</span>
            <strong>
              {quote.volume.toLocaleString()} / {quote.provider}
            </strong>
          </div>
        </div>
      ) : (
        <EmptyState title="等待行情" text="输入标的并刷新或运行流程后展示行情摘要。" />
      )}
    </section>
  );
}

function ReActTracePanel({ result }: { result: ReActResult | null }) {
  return (
    <section className="panel reactPanel">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">ReAct Trace</p>
          <h2>工具调用轨迹</h2>
        </div>
        {result ? <span className="score">{formatPct(result.confidence_score)}</span> : null}
      </div>
      {result ? (
        <>
          <div className="traceList">
            {result.steps.map((step) => (
              <article className="traceStep" key={step.step_number}>
                <div className="traceIndex">{step.step_number}</div>
                <div>
                  <div className="traceMeta">
                    <strong>{step.tool_call.tool_name}</strong>
                    <span className={step.observation.success ? "positive" : "negative"}>
                      {step.observation.success ? "success" : "blocked"}
                    </span>
                  </div>
                  <p>{step.rationale_summary}</p>
                  <small>{step.observation.summary}</small>
                </div>
              </article>
            ))}
          </div>
          <div className="insightBox">
            <strong>Final Answer</strong>
            <p>{result.final_answer}</p>
          </div>
        </>
      ) : (
        <EmptyState title="等待 ReAct 轨迹" text="点击 Run ReAct 后展示只读工具调用和观察结果。" />
      )}
    </section>
  );
}

function MultiAgentPanel({ report }: { report: MultiAgentResearchReport | null }) {
  return (
    <section className="panel multiAgentPanel">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Multi-Agent Research</p>
          <h2>多 Agent 投研委员会</h2>
        </div>
        {report ? (
          <span className="score">{formatPct(report.committee_report.confidence_score)}</span>
        ) : null}
      </div>
      {report ? (
        <>
          <div className="committeeCard">
            <span className={badgeClass(report.committee_report.action_bias)}>
              {report.committee_report.action_bias}
            </span>
            <p>{report.committee_report.summary}</p>
            <small>{report.committee_report.consensus_view}</small>
          </div>
          <div className="findingGrid">
            {report.findings.map((finding) => (
              <article className="findingCard" key={finding.agent_name}>
                <div>
                  <strong>{finding.agent_name}</strong>
                  <span>{formatPct(finding.confidence_score)}</span>
                </div>
                <p>{finding.thesis}</p>
                <ul>
                  {finding.key_points.slice(0, 3).map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </>
      ) : (
        <EmptyState title="等待多 Agent 投研" text="点击 Run Research 或 Automation 后展示四类子 Agent 和委员会结论。" />
      )}
    </section>
  );
}

function ResearchPanel({ research }: { research: ResearchReport | null }) {
  const metricEntries = research ? Object.entries(research.key_metrics).slice(0, 6) : [];

  return (
    <section className="panel resultPanel">
      <div className="sectionHeader compact">
        <div>
          <p className="eyebrow">Research Agent</p>
          <h2>研究报告</h2>
        </div>
        {research ? <span className="score">{formatPct(research.confidence_score)}</span> : null}
      </div>
      {research ? (
        <>
          <p className="lead">{research.summary}</p>
          <div className="metricGrid">
            {metricEntries.map(([key, value]) => (
              <div className="metric" key={key}>
                <span>{key}</span>
                <strong>{String(value)}</strong>
              </div>
            ))}
          </div>
          <h3>估值观点</h3>
          <p>{research.valuation_view}</p>
          <h3>风险提示</h3>
          <ul className="riskList">
            {research.risks.map((risk) => (
              <li key={risk}>{risk}</li>
            ))}
          </ul>
        </>
      ) : (
        <EmptyState title="等待研究报告" text="点击 Run Research 或 Automation 后展示结构化研报。" />
      )}
    </section>
  );
}

function AutomationPanel({ automation }: { automation: AutomationResult | null }) {
  return (
    <section className="panel resultPanel">
      <div className="sectionHeader compact">
        <div>
          <p className="eyebrow">Automation Flow</p>
          <h2>策略与执行结果</h2>
        </div>
        {automation ? (
          <span className={badgeClass(automation.strategy_signal.action)}>
            {automation.strategy_signal.action}
          </span>
        ) : null}
      </div>
      {automation ? (
        <>
          <div className="metricGrid">
            <div className="metric">
              <span>Action</span>
              <strong>{automation.strategy_signal.action}</strong>
            </div>
            <div className="metric">
              <span>Confidence</span>
              <strong>{formatPct(automation.strategy_signal.confidence)}</strong>
            </div>
            <div className="metric">
              <span>Risk</span>
              <strong className={`riskText ${automation.risk_result.risk_level.toLowerCase()}`}>
                {automation.risk_result.risk_level}
              </strong>
            </div>
            <div className="metric">
              <span>Executed</span>
              <strong>{automation.executed ? "Yes" : "No"}</strong>
            </div>
          </div>
          <div className="insightBox">
            <strong>策略理由</strong>
            <p>{automation.strategy_signal.reason}</p>
          </div>
          <div className="insightBox">
            <strong>信号解释</strong>
            <p>{automation.explanation}</p>
          </div>
          {automation.agent_reviews ? (
            <div className="reviewGrid">
              <div className="reviewCard">
                <strong>Strategy Review</strong>
                <span className={automation.agent_reviews.strategy_review.aligned ? "positive" : "negative"}>
                  {automation.agent_reviews.strategy_review.aligned ? "Aligned" : "Needs Review"}
                </span>
                <p>{automation.agent_reviews.strategy_review.review_summary}</p>
              </div>
              <div className="reviewCard">
                <strong>Risk Review</strong>
                <span
                  className={
                    automation.agent_reviews.risk_review.approved_for_auto ? "positive" : "negative"
                  }
                >
                  {automation.agent_reviews.risk_review.approved_for_auto ? "Auto OK" : "Manual Only"}
                </span>
                <p>{automation.agent_reviews.risk_review.review_summary}</p>
              </div>
            </div>
          ) : null}
          <h3>回测</h3>
          <div className="backtestStrip">
            <span>Total {formatPct(automation.backtest_result.total_return)}</span>
            <span>Drawdown {formatPct(automation.backtest_result.max_drawdown)}</span>
            <span>Win {formatPct(automation.backtest_result.win_rate)}</span>
            <span>Trades {automation.backtest_result.trade_count}</span>
          </div>
          <h3>订单</h3>
          <p className="orderLine">{automation.order ? automation.order.order_id : automation.message}</p>
        </>
      ) : (
        <EmptyState title="等待自动化结果" text="点击 Manual Plan 或 Paper Auto 后展示完整流程结果。" />
      )}
    </section>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="emptyState">
      <div className="emptyIcon">AM</div>
      <strong>{title}</strong>
      <p>{text}</p>
    </div>
  );
}
