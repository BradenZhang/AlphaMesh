import type { PortfolioSummary } from "../types";
import { formatMoney, formatPct } from "../utils/format";

interface PortfolioSummaryPanelProps {
  summary: PortfolioSummary | null;
  loading: boolean;
}

export function PortfolioSummaryPanel({ summary, loading }: PortfolioSummaryPanelProps) {
  if (loading) {
    return (
      <section className="railSection">
        <div className="sectionHeading">
          <span>Portfolio</span>
        </div>
        <p className="mutedText">Loading portfolio...</p>
      </section>
    );
  }

  if (!summary) {
    return (
      <section className="railSection">
        <div className="sectionHeading">
          <span>Portfolio</span>
        </div>
        <p className="mutedText">No portfolio data.</p>
      </section>
    );
  }

  const pnlClass = summary.total_unrealized_pnl >= 0 ? "pnlPositive" : "pnlNegative";

  return (
    <section className="railSection">
      <div className="sectionHeading">
        <span>Portfolio</span>
        <small>{summary.holding_count} holdings</small>
      </div>
      <div className="overviewGrid">
        <div className="overviewCard">
          <span>Total Value</span>
          <strong>{formatMoney(summary.total_portfolio_value)}</strong>
        </div>
        <div className="overviewCard">
          <span>Cash</span>
          <strong>{formatMoney(summary.total_cash)}</strong>
        </div>
        <div className="overviewCard">
          <span>Market Value</span>
          <strong>{formatMoney(summary.total_market_value)}</strong>
        </div>
        <div className="overviewCard">
          <span>Unrealized P&amp;L</span>
          <strong className={pnlClass}>
            {formatMoney(summary.total_unrealized_pnl)} ({formatPct(summary.total_unrealized_pnl_pct)})
          </strong>
        </div>
      </div>
      {summary.holdings.length > 0 ? (
        <div className="holdingsTable">
          <div className="holdingsHeader">
            <span>Symbol</span>
            <span>Value</span>
            <span>Weight</span>
            <span>P&amp;L</span>
          </div>
          {summary.holdings.map((h) => (
            <div className="holdingsRow" key={h.holding_id}>
              <strong>{h.symbol}</strong>
              <span>{formatMoney(h.market_value)}</span>
              <span>{formatPct(h.weight)}</span>
              <span className={h.unrealized_pnl >= 0 ? "pnlPositive" : "pnlNegative"}>
                {formatMoney(h.unrealized_pnl)}
              </span>
            </div>
          ))}
        </div>
      ) : null}
      {Object.keys(summary.sector_breakdown).length > 0 ? (
        <div className="sectorBreakdown">
          <small className="breakdownLabel">Sector Breakdown</small>
          {Object.entries(summary.sector_breakdown).map(([sector, weight]) => (
            <div className="breakdownRow" key={sector}>
              <span>{sector}</span>
              <span>{formatPct(weight)}</span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
