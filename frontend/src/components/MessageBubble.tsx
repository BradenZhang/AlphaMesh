import { useState } from "react";
import type {
  AutomationResult,
  ChatArtifact,
  ChatMessage,
  MultiAgentResearchReport,
  PaperOrder,
  ReActResult
} from "../types";
import { formatDateTime, formatMoney, formatPct } from "../utils/format";
import { WorkflowTimeline } from "./WorkflowTimeline";

function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen).trimEnd() + "...";
}

function getArtifactPreview(artifact: ChatArtifact): string | null {
  switch (artifact.type) {
    case "react_trace":
      return artifact.payload.final_answer ? truncate(artifact.payload.final_answer, 120) : null;
    case "research_report":
      return artifact.payload.summary ? truncate(artifact.payload.summary, 120) : null;
    case "multi_agent_report":
      return artifact.payload.committee_report.summary
        ? truncate(artifact.payload.committee_report.summary, 120)
        : null;
    case "automation_result":
      return artifact.payload.explanation ? truncate(artifact.payload.explanation, 120) : null;
    case "paper_order": {
      const o = artifact.payload;
      return `${o.side} ${o.quantity} ${o.symbol} @ ${o.limit_price ? formatMoney(o.limit_price) : "market"}`;
    }
    default:
      return null;
  }
}

function MessageStatusIndicator({ message }: { message: ChatMessage }) {
  const isPending = message.message_id.startsWith("pending-");
  const isError = message.status === "error";

  if (isPending && message.role === "assistant") {
    return (
      <span className="messageStatusIndicator pending" title="Processing...">
        <svg viewBox="0 0 16 16" width="14" height="14">
          <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="20 12" />
        </svg>
      </span>
    );
  }
  if (isError) {
    return (
      <span className="messageStatusIndicator error" title="Error">
        <svg viewBox="0 0 16 16" width="14" height="14">
          <circle cx="8" cy="8" r="6" fill="currentColor" opacity="0.15" />
          <line x1="8" y1="5" x2="8" y2="9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <circle cx="8" cy="11" r="0.8" fill="currentColor" />
        </svg>
      </span>
    );
  }
  if (message.role === "assistant" && !isPending) {
    return (
      <span className="messageStatusIndicator completed" title="Completed">
        <svg viewBox="0 0 16 16" width="14" height="14">
          <polyline points="4,8 7,11 12,5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
    );
  }
  return null;
}

export function MessageBubble({ message, onArtifactOpen }: {
  message: ChatMessage;
  onArtifactOpen?: (artifact: ChatArtifact) => void;
}) {
  const isError = message.status === "error";
  return (
    <article className={`messageRow ${message.role === "user" ? "user" : "assistant"}`}>
      <div className={`messageAvatar ${message.role === "user" ? "user" : "assistant"}`}>
        {message.role === "user" ? "YU" : "AM"}
      </div>
      <div className={`messageBubble ${message.role === "user" ? "user" : "assistant"} ${isError ? "error" : ""}`}>
        <div className="messageMeta">
          <span>
            {message.role === "user" ? "You" : "AlphaMesh"}
            <MessageStatusIndicator message={message} />
          </span>
          <small>
            {message.action ? `${message.action.replaceAll("_", " ")} / ` : ""}
            {formatDateTime(message.created_at)}
          </small>
        </div>
        <p>{message.content}</p>
        {message.artifacts.length > 0 ? (
          <div className="artifactStack">
            {message.artifacts.map((artifact) => (
              <ArtifactCard
                artifact={artifact}
                key={`${message.message_id}-${artifact.type}-${artifact.title}`}
                onOpen={onArtifactOpen}
              />
            ))}
          </div>
        ) : null}
      </div>
    </article>
  );
}

function ArtifactCard({ artifact, onOpen }: {
  artifact: ChatArtifact;
  onOpen?: (artifact: ChatArtifact) => void;
}) {
  const [open, setOpen] = useState(false);
  const preview = getArtifactPreview(artifact);

  return (
    <div className={`artifactCard ${open ? "open" : ""}`}>
      <button
        className="artifactHeader"
        onClick={() => setOpen(!open)}
        type="button"
      >
        <strong>{artifact.title}</strong>
        <span>{artifact.type.replaceAll("_", " ")}</span>
        {onOpen ? (
          <span
            className="artifactExpand"
            onClick={(e) => { e.stopPropagation(); onOpen(artifact); }}
            role="button"
            tabIndex={0}
            title="Open in detail view"
          >
            Expand
          </span>
        ) : null}
      </button>
      {preview && !open ? <p className="artifactPreview">{preview}</p> : null}
      {open ? <div className="artifactBody">{renderArtifactBody(artifact)}</div> : null}
    </div>
  );
}

export function renderArtifactBody(artifact: ChatArtifact, onRetry?: () => void) {
  switch (artifact.type) {
    case "react_trace":
      return <ReactTraceArtifactView result={artifact.payload} />;
    case "research_report":
      return <ResearchArtifactView report={artifact.payload} />;
    case "multi_agent_report":
      return <MultiAgentArtifactView report={artifact.payload} />;
    case "automation_result":
      return <AutomationArtifactView result={artifact.payload} onRetry={onRetry} />;
    case "paper_order":
      return <PaperOrderArtifactView order={artifact.payload} />;
    default: {
      const _exhaustive: never = artifact;
      return null;
    }
  }
}

function ReactTraceArtifactView({ result }: { result: ReActResult }) {
  return (
    <div className="artifactContent">
      {result.run_steps?.length ? <WorkflowTimeline runSteps={result.run_steps} /> : null}
      <div className="metricStrip">
        <Metric label="Confidence" value={formatPct(result.confidence_score)} />
        <Metric label="Steps" value={String(result.steps.length)} />
      </div>
      <div className="stepList">
        {result.steps.map((step) => (
          <div className="stepCard" key={step.step_number}>
            <strong>
              {step.step_number}. {step.tool_call.tool_name}
            </strong>
            <p>{step.rationale_summary}</p>
            <small>{step.observation.summary}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function ResearchArtifactView({ report }: { report: MultiAgentResearchReport["research_report"] }) {
  return (
    <div className="artifactContent">
      <p className="artifactLead">{report.summary}</p>
      <div className="metricStrip">
        <Metric label="Confidence" value={formatPct(report.confidence_score)} />
        <Metric label="Risks" value={String(report.risks.length)} />
      </div>
      <div className="tokenList">
        {Object.entries(report.key_metrics)
          .slice(0, 6)
          .map(([key, value]) => (
            <span className="tokenChip" key={key}>
              {key}: {String(value)}
            </span>
          ))}
      </div>
      <p className="artifactMuted">{report.valuation_view}</p>
    </div>
  );
}

function MultiAgentArtifactView({ report }: { report: MultiAgentResearchReport }) {
  return (
    <div className="artifactContent">
      <div className="metricStrip">
        <Metric label="Bias" value={report.committee_report.action_bias} />
        <Metric label="Confidence" value={formatPct(report.committee_report.confidence_score)} />
      </div>
      <p className="artifactLead">{report.committee_report.summary}</p>
      <div className="findingList">
        {report.findings.map((finding) => (
          <div className="findingRow" key={finding.agent_name}>
            <strong>{finding.agent_name}</strong>
            <span>{finding.thesis}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AutomationArtifactView({ result, onRetry }: { result: AutomationResult; onRetry?: () => void }) {
  return (
    <div className="artifactContent">
      {result.run_steps?.length ? <WorkflowTimeline runSteps={result.run_steps} onRetry={onRetry} /> : null}
      <div className="metricStrip">
        <Metric label="Action" value={result.strategy_signal.action} />
        <Metric label="Confidence" value={formatPct(result.strategy_signal.confidence)} />
        <Metric label="Risk" value={result.risk_result.risk_level} />
        <Metric label="Executed" value={result.executed ? "Yes" : "No"} />
      </div>
      <p className="artifactLead">{result.explanation}</p>
      <div className="tokenList">
        <span className="tokenChip">Return: {formatPct(result.backtest_result.total_return)}</span>
        <span className="tokenChip">
          Drawdown: {formatPct(result.backtest_result.max_drawdown)}
        </span>
        <span className="tokenChip">Win rate: {formatPct(result.backtest_result.win_rate)}</span>
        <span className="tokenChip">Trades: {result.backtest_result.trade_count}</span>
        {result.backtest_result.validation_badge ? (
          <span className={`tokenChip badge-${result.backtest_result.validation_badge}`}>
            WF Badge: {result.backtest_result.validation_badge}
          </span>
        ) : null}
        {result.backtest_result.slippage_bps > 0 ? (
          <span className="tokenChip">Slippage: {result.backtest_result.slippage_bps}bps</span>
        ) : null}
      </div>
      {result.backtest_result.oos_total_return != null ? (
        <div className="tokenList">
          <span className="tokenChip">OOS Return: {formatPct(result.backtest_result.oos_total_return)}</span>
          <span className="tokenChip">OOS DD: {formatPct(result.backtest_result.oos_max_drawdown ?? 0)}</span>
          <span className="tokenChip">OOS Sharpe: {(result.backtest_result.oos_sharpe_ratio ?? 0).toFixed(2)}</span>
        </div>
      ) : null}
      {result.agent_reviews ? (
        <div className="reviewStack">
          <div className="reviewCard">
            <strong>Strategy Review</strong>
            <p>{result.agent_reviews.strategy_review.review_summary}</p>
          </div>
          <div className="reviewCard">
            <strong>Risk Review</strong>
            <p>{result.agent_reviews.risk_review.review_summary}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function PaperOrderArtifactView({ order }: { order: PaperOrder }) {
  return (
    <div className="artifactContent">
      <div className="metricStrip">
        <Metric label="Side" value={order.side} />
        <Metric label="Status" value={order.status} />
        <Metric label="Qty" value={String(order.quantity)} />
      </div>
      <p className="artifactLead">{order.order_id}</p>
      <p className="artifactMuted">
        {order.limit_price ? formatMoney(order.limit_price) : "Market order"} /{" "}
        {order.estimated_amount ? formatMoney(order.estimated_amount) : "n/a"}
      </p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metricCard">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
