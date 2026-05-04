import type { RebalanceWorkflowResult } from "../types";
import { formatMoney, formatPct } from "../utils/format";

interface RebalanceDrawerProps {
  open: boolean;
  result: RebalanceWorkflowResult | null;
  onClose: () => void;
}

export function RebalanceDrawer({ open, result, onClose }: RebalanceDrawerProps) {
  if (!open || !result) return null;

  return (
    <div className="drawerOverlay" onClick={onClose}>
      <div className="drawerPanel" onClick={(e) => e.stopPropagation()}>
        <div className="drawerHeader">
          <h3>Rebalance Result</h3>
          <button className="ghostButton" onClick={onClose} type="button">
            Close
          </button>
        </div>
        <div className="drawerBody">
          <p className="rebalanceMessage">{result.message}</p>

          {result.portfolio_manager_report ? (
            <div className="rebalanceSection">
              <h4>Portfolio Manager</h4>
              <p>{result.portfolio_manager_report.portfolio_context_summary}</p>
              <p>
                <small>Confidence: {formatPct(result.portfolio_manager_report.overall_confidence)}</small>
              </p>
              {result.portfolio_manager_report.concentration_warnings.length > 0 ? (
                <div className="riskWarnings">
                  {result.portfolio_manager_report.concentration_warnings.map((w, i) => (
                    <span key={i} className="warningBadge">{w}</span>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}

          {result.rebalance_proposal ? (
            <div className="rebalanceSection">
              <h4>Proposal ({result.rebalance_proposal.orders.length} orders)</h4>
              <p>
                Turnover: {formatPct(result.rebalance_proposal.estimated_turnover)} |
                Cash after: {formatMoney(result.rebalance_proposal.cash_after)}
              </p>
              <div className="proposalTable">
                <div className="proposalHeader">
                  <span>Symbol</span>
                  <span>Side</span>
                  <span>Qty</span>
                  <span>Amount</span>
                  <span>Target</span>
                </div>
                {result.rebalance_proposal.orders.map((order, i) => (
                  <div className="proposalRow" key={i}>
                    <strong>{order.symbol}</strong>
                    <span className={order.side === "BUY" ? "sideBuy" : "sideSell"}>
                      {order.side}
                    </span>
                    <span>{order.quantity}</span>
                    <span>{formatMoney(order.estimated_amount)}</span>
                    <span>{formatPct(order.target_weight)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {result.risk_review ? (
            <div className="rebalanceSection">
              <h4>Risk Review</h4>
              <p>
                <span className={result.risk_review.approved ? "approvedBadge" : "rejectedBadge"}>
                  {result.risk_review.approved ? "APPROVED" : "REJECTED"}
                </span>
                <span className={`riskLevel-${result.risk_review.risk_level}`}>
                  {result.risk_review.risk_level}
                </span>
              </p>
              <ul>
                {result.risk_review.reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {result.executed_orders.length > 0 ? (
            <div className="rebalanceSection">
              <h4>Executed Orders</h4>
              <div className="railFeed">
                {result.executed_orders.map((order, i) => (
                  <div className="feedCard" key={i}>
                    <strong>{(order as Record<string, unknown>).symbol as string}</strong>
                    <span>
                      {(order as Record<string, unknown>).side as string}{" "}
                      {(order as Record<string, unknown>).quantity as number}
                    </span>
                    <small>{(order as Record<string, unknown>).status as string}</small>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {result.run_steps.length > 0 ? (
            <div className="rebalanceSection">
              <h4>Workflow Steps</h4>
              <div className="railFeed">
                {result.run_steps.map((step, i) => {
                  const s = step as Record<string, unknown>;
                  return (
                    <div className="feedCard" key={i}>
                      <strong>{s.step as string}</strong>
                      <span>{s.status as string}</span>
                      {typeof s.latency_ms === "number" ? (
                        <small>{s.latency_ms}ms</small>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
