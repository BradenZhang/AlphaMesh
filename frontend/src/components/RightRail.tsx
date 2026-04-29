import type { AgentRun, AgentStatus, LLMProfileListResponse, PaperOrder, StrategyName } from "../types";
import { formatDateTime } from "../utils/format";

interface ContextDraft {
  title: string;
  symbol: string;
  llmProfileId: string;
  strategyName: StrategyName;
}

interface RightRailProps {
  contextDraft: ContextDraft;
  profiles: LLMProfileListResponse["profiles"];
  activeProfileId: string;
  sidebarStatus: {
    health: string;
    agentStatus: AgentStatus | null;
    profiles: LLMProfileListResponse | null;
  };
  sidebarError: string | null;
  activityRuns: AgentRun[];
  activityOrders: PaperOrder[];
  activityError: string | null;
  latestRun: AgentRun | null;
  latestOrder: PaperOrder | null;
  onContextDraftChange: (update: Partial<ContextDraft>) => void;
  onSaveContext: () => void;
  onRefreshStatus: () => void;
}

export function RightRail({
  contextDraft,
  profiles,
  sidebarStatus,
  sidebarError,
  activityRuns,
  activityOrders,
  activityError,
  latestRun,
  latestOrder,
  onContextDraftChange,
  onSaveContext,
  onRefreshStatus
}: RightRailProps) {
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
        </div>
      </section>

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
