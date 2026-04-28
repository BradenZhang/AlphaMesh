export type AgentStatus = {
  provider: string;
  model: string;
  is_mock: boolean;
};

export type AgentRun = {
  run_id: string;
  run_type: string;
  status: string;
  symbol: string | null;
  provider: string | null;
  model: string | null;
  latency_ms: number;
  created_at: string;
  error_message: string | null;
};

export type ResearchReport = {
  symbol: string;
  summary: string;
  key_metrics: Record<string, number | string>;
  valuation_view: string;
  risks: string[];
  confidence_score: number;
};

export type Quote = {
  symbol: string;
  price: number;
  open: number;
  high: number;
  low: number;
  previous_close: number;
  volume: number;
  provider: string;
  timestamp: string;
};

export type StrategyName = "moving_average_cross" | "valuation_band";

export type PaperOrder = {
  order_id: string;
  symbol: string;
  side: string;
  quantity: number;
  limit_price: number | null;
  estimated_amount: number | null;
  status: string;
  created_at: string;
};

export type AutomationResult = {
  symbol: string;
  mode: string;
  research_report: ResearchReport;
  strategy_signal: {
    action: string;
    confidence: number;
    reason: string;
    suggested_position_pct: number;
  };
  backtest_result: {
    total_return: number;
    max_drawdown: number;
    win_rate: number;
    sharpe_ratio: number;
    trade_count: number;
  };
  risk_result: {
    approved: boolean;
    risk_level: string;
    reasons: string[];
  };
  explanation: string;
  executed: boolean;
  message: string;
  order: {
    order_id: string;
    side: string;
    quantity: number;
    status: string;
  } | null;
};
