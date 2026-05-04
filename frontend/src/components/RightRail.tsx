import type { AgentRun, AgentStatus, InvestmentCase, LLMCall, LLMProfileListResponse, PaperOrder, PortfolioSummary, ProviderHealth, ProviderName, StrategyName, WatchlistItem } from "../types";
import { formatDateTime, formatMoney, formatPct, formatTokens } from "../utils/format";
import { PortfolioSummaryPanel } from "./PortfolioSummaryPanel";
import { WatchlistPanel } from "./WatchlistPanel";

interface ContextDraft {
  title: string;
  symbol: string;
  llmProfileId: string;
  strategyName: StrategyName;
  marketProvider: ProviderName;
  executionProvider: ProviderName;
  accountProvider: ProviderName;
}

interface RightRailProps {
  contextDraft: ContextDraft;
  profiles: LLMProfileListResponse["profiles"];
  activeProfileId: string;
  sidebarStatus: {
    health: string;
    agentStatus: AgentStatus | null;
    profiles: LLMProfileListResponse | null;
    providerHealth: ProviderHealth[];
  };
  sidebarError: string | null;
  activityRuns: AgentRun[];
  activityOrders: PaperOrder[];
  activityError: string | null;
  llmCalls: LLMCall[];
  cases: InvestmentCase[];
  latestRun: AgentRun | null;
  latestOrder: PaperOrder | null;
  watchlist: WatchlistItem[];
  portfolioSummary: PortfolioSummary | null;
  portfolioLoading: boolean;
  onContextDraftChange: (update: Partial<ContextDraft>) => void;
  onSaveContext: () => void;
  onRefreshStatus: () => void;
  onAddWatchlist: (symbol: string) => void;
  onRemoveWatchlist: (itemId: string) => void;
  onBatchResearch: () => void;
  onRebalance: () => void;
}

export function RightRail({
  contextDraft,
  profiles,
  sidebarStatus,
  sidebarError,
  activityRuns,
  activityOrders,
  activityError,
  llmCalls,
  cases,
  latestRun,
  latestOrder,
  watchlist,
  portfolioSummary,
  portfolioLoading,
  onContextDraftChange,
  onSaveContext,
  onRefreshStatus,
  onAddWatchlist,
  onRemoveWatchlist,
  onBatchResearch,
  onRebalance
}: RightRailProps) {
  const providerOptions: ProviderName[] = ["mock", "longbridge", "futu", "eastmoney", "ibkr"];
  const marketHealth = sidebarStatus.providerHealth.filter((item) => item.capability === "market");

  return (
    <aside className="rightRail">
      <section className="railSection">
        <div className="sectionHeading">
          <span>Run Context</span>
          <button className="ghostButton" onClick={onSaveContext} type="button">
            Save
          </button>
        </div>
        <div className="fieldGrid">
          <label>
            Title
            <input
              onChange={(event) => onContextDraftChange({ title: event.target.value })}
              value={contextDraft.title}
            />
          </label>
          <label>
            Symbol
            <input
              onChange={(event) => onContextDraftChange({ symbol: event.target.value.toUpperCase() })}
              placeholder="AAPL"
              value={contextDraft.symbol}
            />
          </label>
          <label>
            Model Profile
            <select
              onChange={(event) => onContextDraftChange({ llmProfileId: event.target.value })}
              value={contextDraft.llmProfileId}
            >
              <option value="">Default</option>
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Strategy
            <select
              onChange={(event) => onContextDraftChange({ strategyName: event.target.value as StrategyName })}
              value={contextDraft.strategyName}
            >
              <option value="moving_average_cross">Moving Average Cross</option>
              <option value="valuation_band">Valuation Band</option>
            </select>
          </label>
          <label>
            Market Provider
            <select
              onChange={(event) => onContextDraftChange({ marketProvider: event.target.value as ProviderName })}
              value={contextDraft.marketProvider}
            >
              {providerOptions.map((provider) => (
                <option key={`market-${provider}`} value={provider}>
                  {provider}
                </option>
              ))}
            </select>
          </label>
          <label>
            Execution Provider
            <select
              onChange={(event) => onContextDraftChange({ executionProvider: event.target.value as ProviderName })}
              value={contextDraft.executionProvider}
            >
              {providerOptions.filter((item) => item !== "eastmoney").map((provider) => (
                <option key={`execution-${provider}`} value={provider}>
                  {provider}
                </option>
              ))}
            </select>
          </label>
          <label>
            Account Provider
            <select
              onChange={(event) => onContextDraftChange({ accountProvider: event.target.value as ProviderName })}
              value={contextDraft.accountProvider}
            >
              {providerOptions.filter((item) => item !== "eastmoney").map((provider) => (
                <option key={`account-${provider}`} value={provider}>
                  {provider}
                </option>
              ))}
            </select>
          </label>
        </div>
        {marketHealth.length > 0 ? (
          <p className="mutedText">
            Provider health: {marketHealth.map((item) => `${item.provider}=${item.available ? "up" : "down"}`).join(" / ")}
          </p>
        ) : null}
      </section>

      <PortfolioSummaryPanel summary={portfolioSummary} loading={portfolioLoading} />

      <WatchlistPanel
        items={watchlist}
        onAdd={onAddWatchlist}
        onRemove={onRemoveWatchlist}
        onBatchResearch={onBatchResearch}
        onRebalance={onRebalance}
        loading={portfolioLoading}
      />

      <section className="railSection">
        <div className="sectionHeading">
          <span>System Status</span>
          <button className="ghostButton" onClick={onRefreshStatus} type="button">
            Refresh
          </button>
        </div>
        <div className="statusStack">
          <StatusTile label="Backend" value={sidebarStatus.health} />
          <StatusTile label="Provider" value={sidebarStatus.agentStatus?.provider ?? "loading"} />
          <StatusTile label="Model" value={sidebarStatus.agentStatus?.model ?? "loading"} />
        </div>
        {sidebarError ? <p className="errorText">{sidebarError}</p> : null}
      </section>

      <section className="railSection">
        <div className="sectionHeading">
          <span>Latest Activity</span>
          <small>{activityRuns.length + activityOrders.length}</small>
        </div>
        <div className="overviewGrid">
          <div className="overviewCard">
            <span>Last run</span>
            <strong>{latestRun?.run_type ?? "No runs yet"}</strong>
            <small>
              {latestRun
                ? `${latestRun.status} / ${latestRun.latency_ms}ms / ${latestRun.symbol ?? "-"}`
                : "Research and automation runs will show up here."}
            </small>
          </div>
          <div className="overviewCard">
            <span>Last order</span>
            <strong>{latestOrder?.symbol ?? "No paper order"}</strong>
            <small>
              {latestOrder
                ? `${latestOrder.side} / ${latestOrder.status} / ${formatDateTime(latestOrder.created_at)}`
                : "Paper automation output will show up here."}
            </small>
          </div>
        </div>
        <div className="railFeed">
          {activityRuns.slice(0, 4).map((run) => (
            <div className="feedCard" key={run.run_id}>
              <strong>{run.run_type}</strong>
              <span>{run.symbol ?? "-"}</span>
              <small>
                {run.status}
                <span className="dotDivider" />
                {run.latency_ms}ms
              </small>
            </div>
          ))}
          {activityOrders.slice(0, 3).map((order) => (
            <div className="feedCard" key={order.order_id}>
              <strong>{order.symbol}</strong>
              <span>
                {order.side} / {order.status}
              </span>
              <small>{formatDateTime(order.created_at)}</small>
            </div>
          ))}
        </div>
        {activityError ? <p className="errorText">{activityError}</p> : null}
      </section>

      <section className="railSection">
        <div className="sectionHeading">
          <span>Recent Cases</span>
          <small>{cases.length}</small>
        </div>
        <div className="railFeed">
          {cases.slice(0, 6).map((item) => (
            <div className="feedCard" key={item.case_id}>
              <strong>
                <span className={`decisionBadge decision-${item.decision}`}>{item.decision.toUpperCase()}</span>
                {item.symbol}
              </strong>
              <span>{formatPct(item.confidence)} confidence</span>
              <small>
                {item.outcome ?? "pending"}
                <span className="dotDivider" />
                {formatDateTime(item.created_at)}
              </small>
            </div>
          ))}
          {cases.length === 0 ? <p className="mutedText">No investment cases yet.</p> : null}
        </div>
      </section>

      <section className="railSection">
        <div className="sectionHeading">
          <span>LLM Cost Monitor</span>
          <small>{llmCalls.length} calls</small>
        </div>
        <CostMonitorSummary llmCalls={llmCalls} />
        <div className="railFeed">
          {llmCalls.slice(0, 8).map((call) => (
            <div className="feedCard" key={call.call_id}>
              <strong>
                {call.provider ?? "?"}/{call.model ?? "?"}
              </strong>
              <span>
                {formatTokens(call.prompt_tokens)} in
                <span className="dotDivider" />
                {formatTokens(call.completion_tokens)} out
              </span>
              <small>
                {formatMoney(call.estimated_cost_usd)}
                <span className="dotDivider" />
                {call.latency_ms}ms
                <span className="dotDivider" />
                {call.call_type}
              </small>
            </div>
          ))}
        </div>
      </section>
    </aside>
  );
}

function StatusTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="statusTile">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function CostMonitorSummary({ llmCalls }: { llmCalls: LLMCall[] }) {
  const totalCost = llmCalls.reduce((sum, call) => sum + call.estimated_cost_usd, 0);
  const totalTokens = llmCalls.reduce((sum, call) => sum + call.total_tokens, 0);
  return (
    <div className="overviewGrid">
      <div className="overviewCard">
        <span>Session Cost</span>
        <strong>{formatMoney(totalCost)}</strong>
      </div>
      <div className="overviewCard">
        <span>Total Tokens</span>
        <strong>{formatTokens(totalTokens)}</strong>
      </div>
    </div>
  );
}
