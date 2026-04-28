import { useEffect, useMemo, useState } from "react";
import {
  fetchAgentRuns,
  fetchAgentStatus,
  fetchHealth,
  fetchPaperOrders,
  fetchQuote,
  runAutomation,
  runResearch
} from "./api";
import type {
  AgentRun,
  AgentStatus,
  AutomationResult,
  PaperOrder,
  Quote,
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
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [orders, setOrders] = useState<PaperOrder[]>([]);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [strategyName, setStrategyName] = useState<StrategyName>("moving_average_cross");
  const [research, setResearch] = useState<ResearchReport | null>(null);
  const [automation, setAutomation] = useState<AutomationResult | null>(null);
  const [state, setState] = useState<LoadState>("idle");
  const [error, setError] = useState<string | null>(null);

  const normalizedSymbol = useMemo(() => symbol.trim().toUpperCase() || "AAPL", [symbol]);
  const isLoading = state === "loading";

  async function refreshStatus() {
    const [healthPayload, statusPayload, runPayload, orderPayload, quotePayload] = await Promise.all([
      fetchHealth(),
      fetchAgentStatus(),
      fetchAgentRuns(),
      fetchPaperOrders(),
      fetchQuote(normalizedSymbol)
    ]);
    setHealth(`${healthPayload.status} / ${healthPayload.service}`);
    setAgentStatus(statusPayload);
    setRuns(runPayload);
    setOrders(orderPayload);
    setQuote(quotePayload);
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
      const report = await runResearch(normalizedSymbol);
      setResearch(report);
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
      const result = await runAutomation(normalizedSymbol, mode, strategyName);
      setAutomation(result);
      setResearch(result.research_report);
      setState("success");
      await refreshStatus();
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "Automation request failed.");
    }
  }

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">AlphaMesh MVP Dashboard</p>
          <h1>多 Agent 投研自动化控制台</h1>
          <p className="heroText">
            用 Mock 行情、LLM Research Agent、策略、回测和风控串联完整 paper trading
            流程。当前页面只用于 MVP 验证，不进行真实交易。
          </p>
          <div className="flowStrip">
            {["Market", "Research", "Strategy", "Backtest", "Risk", "Paper Order"].map((step) => (
              <span key={step}>{step}</span>
            ))}
          </div>
        </div>
        <div className="statusGrid">
          <StatusCard label="Backend" value={health} accent="green" />
          <StatusCard
            label="LLM Provider"
            value={agentStatus?.provider ?? "loading"}
            accent={agentStatus?.is_mock ? "blue" : "purple"}
          />
          <StatusCard label="Model" value={agentStatus?.model ?? "loading"} accent="slate" />
        </div>
      </section>

      <section className="panel controls">
        <div className="controlIntro">
          <p className="eyebrow">Command Center</p>
          <h2>运行投研流程</h2>
          <p className="muted">输入标的后，可先单独生成研报，也可以直接跑完整自动化计划。</p>
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
          <button className="secondary" disabled={isLoading} onClick={() => handleAutomation("manual")}>
            Manual Plan
          </button>
          <button className="success" disabled={isLoading} onClick={() => handleAutomation("paper_auto")}>
            Paper Auto
          </button>
        </div>
      </section>

      {error ? <div className="alert">请求失败：{error}</div> : null}

      <MarketPanel quote={quote} />

      <section className="grid">
        <ResearchPanel research={research} />
        <AutomationPanel automation={automation} />
      </section>

      <section className="panel">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Paper Trading</p>
            <h2>最近 Paper 订单</h2>
          </div>
          <span className="badge hold">{orders.length} orders</span>
        </div>
        <div className="orderGrid">
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

      <section className="panel">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Observability</p>
            <h2>Agent Run 日志</h2>
          </div>
          <button className="ghost" onClick={() => refreshStatus()}>
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
    </main>
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
