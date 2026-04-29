import type {
  AutomationResult,
  ChatArtifact,
  ChatMessage,
  MultiAgentResearchReport,
  PaperOrder,
  ReActResult
} from "../types";
import { formatDateTime, formatMoney, formatPct } from "../utils/format";

export function MessageBubble({ message }: { message: ChatMessage }) {
  return (
    <article className={`messageRow ${message.role === "user" ? "user" : "assistant"}`}>
      <div className={`messageAvatar ${message.role === "user" ? "user" : "assistant"}`}>
        {message.role === "user" ? "YU" : "AM"}
      </div>
      <div className={`messageBubble ${message.role === "user" ? "user" : "assistant"}`}>
        <div className="messageMeta">
          <span>{message.role === "user" ? "You" : "AlphaMesh"}</span>
          <small>
            {message.action ? `${message.action.replaceAll("_", " ")} / ` : ""}
            {formatDateTime(message.created_at)}
          </small>
        </div>
        <p>{message.content}</p>
        {message.artifacts.length > 0 ? (
          <div className="artifactStack">
            {message.artifacts.map((artifact) => (
              <ArtifactCard artifact={artifact} key={`${message.message_id}-${artifact.type}-${artifact.title}`} />
            ))}
          </div>
        ) : null}
      </div>
    </article>
  );
}

function ArtifactCard({ artifact }: { artifact: ChatArtifact }) {
  return (
    <details className="artifactCard">
      <summary>
        <strong>{artifact.title}</strong>
        <span>{artifact.type.replaceAll("_", " ")}</span>
      </summary>
      <div className="artifactBody">{renderArtifactBody(artifact)}</div>
    </details>
  );
}

function renderArtifactBody(artifact: ChatArtifact) {
  switch (artifact.type) {
    case "react_trace":
      return <ReactTraceArtifactView result={artifact.payload} />;
    case "research_report":
      return <ResearchArtifactView report={artifact.payload} />;
    case "multi_agent_report":
      return <MultiAgentArtifactView report={artifact.payload} />;
    case "automation_result":
      return <AutomationArtifactView result={artifact.payload} />;
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

function AutomationArtifactView({ result }: { result: AutomationResult }) {
  return (
    <div className="artifactContent">
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
      </div>
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
