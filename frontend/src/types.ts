export type AgentStatus = {
  provider: "openai" | "anthropic" | "gemini" | "mock" | (string & {});
  model: string;
  is_mock: boolean;
};

export type ProviderName =
  | "mock"
  | "longbridge"
  | "futu"
  | "eastmoney"
  | "ibkr"
  | (string & {});

export type ProviderHealth = {
  provider: ProviderName;
  capability: "market" | "execution" | "account" | (string & {});
  transport: string;
  available: boolean;
  message: string | null;
};

export type LLMProfile = {
  id: string;
  label: string;
  provider: string;
  model: string;
  base_url_configured: boolean;
  api_key_configured: boolean;
  is_mock: boolean;
  is_default: boolean;
};

export type LLMProfileListResponse = {
  default_profile_id: string;
  profiles: LLMProfile[];
};

export type AgentRunStatus = "pending" | "running" | "completed" | "failed";
export type AgentRunType = "research" | "automation" | "manual_plan" | (string & {});

export type AgentRun = {
  run_id: string;
  run_type: AgentRunType;
  status: AgentRunStatus;
  symbol: string | null;
  provider: string | null;
  model: string | null;
  latency_ms: number;
  created_at: string;
  error_message: string | null;
  market_provider: string | null;
  execution_provider: string | null;
  account_provider: string | null;
};

export type LLMCall = {
  call_id: string;
  call_type: string;
  symbol: string | null;
  provider: string | null;
  model: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  estimated_cost_usd: number;
  created_at: string;
};

export type ResearchReport = {
  symbol: string;
  summary: string;
  key_metrics: Record<string, number | string>;
  valuation_view: string;
  risks: string[];
  confidence_score: number;
  data_sources: string[];
};

export type AgentFinding = {
  agent_name: string;
  symbol: string;
  thesis: string;
  key_points: string[];
  metrics: Record<string, number | string>;
  risks: string[];
  confidence_score: number;
  data_sources: string[];
};

export type InvestmentCommitteeReport = {
  symbol: string;
  summary: string;
  consensus_view: string;
  key_debates: string[];
  action_bias: "buy" | "sell" | "hold" | (string & {});
  confidence_score: number;
};

export type MultiAgentResearchReport = {
  symbol: string;
  findings: AgentFinding[];
  committee_report: InvestmentCommitteeReport;
  research_report: ResearchReport;
  case_id?: string;
};

export type StrategyReviewReport = {
  symbol: string;
  aligned: boolean;
  review_summary: string;
  strengths: string[];
  concerns: string[];
  confidence_score: number;
};

export type RiskReviewReport = {
  symbol: string;
  approved_for_auto: boolean;
  review_summary: string;
  risk_flags: string[];
  confidence_score: number;
};

export type AgentReviewBundle = {
  strategy_review: StrategyReviewReport;
  risk_review: RiskReviewReport;
};

export type RunStepStatus = "pending" | "running" | "completed" | "failed" | "skipped";

export type RunStep = {
  step_id: string;
  label: string;
  status: RunStepStatus;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number;
  summary: string | null;
  error: string | null;
};

export type ReActStep = {
  step_number: number;
  rationale_summary: string;
  tool_call: {
    tool_name: string;
    arguments: Record<string, unknown>;
  };
  observation: {
    success: boolean;
    summary: string;
    data: Record<string, unknown>;
  };
};

export type ReActResult = {
  symbol: string;
  llm_profile_id: string | null;
  steps: ReActStep[];
  final_answer: string;
  confidence_score: number;
  run_steps?: RunStep[];
};

export type MemoryRecord = {
  memory_id: string;
  scope: "short_term" | "long_term";
  memory_type: string;
  symbol: string | null;
  user_id: string;
  content: string;
  content_hash: string | null;
  token_keywords: string[];
  metadata: Record<string, unknown>;
  importance_score: number;
  token_estimate: number;
  expires_at: string | null;
  created_at: string;
};

export type MemoryContext = {
  symbol: string | null;
  user_id: string;
  query: string | null;
  context: string;
  memories: MemoryRecord[];
  token_budget: number;
  token_estimate: number;
  compacted: boolean;
  compression_triggered: boolean;
  compression_strategy: "map_reduce" | "none" | (string & {});
  budget_allocation: Record<string, number>;
  compression_token_usage: Record<string, number>;
};

export type MemoryStats = {
  short_term_count: number;
  long_term_count: number;
  total_count: number;
  total_token_estimate: number;
  index_loaded_count: number;
  index_keyword_count: number;
  index_loaded_at: string | null;
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
export type ReplyAction = "chat" | "research" | "manual_plan" | "paper_auto";

export type PaperOrderSide = "buy" | "sell";
export type PaperOrderStatus = "pending" | "filled" | "cancelled" | (string & {});

export type PaperOrder = {
  order_id: string;
  symbol: string;
  side: PaperOrderSide;
  quantity: number;
  limit_price: number | null;
  estimated_amount: number | null;
  status: PaperOrderStatus;
  created_at: string;
  paper?: boolean;
};

export type AutomationResult = {
  symbol: string;
  mode: "manual" | "paper_auto" | "live_auto" | (string & {});
  research_report: ResearchReport;
  strategy_signal: {
    action: "buy" | "sell" | "hold" | (string & {});
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
    slippage_bps: number;
    commission_per_trade: number;
    oos_total_return: number | null;
    oos_max_drawdown: number | null;
    oos_sharpe_ratio: number | null;
    is_total_return: number | null;
    is_max_drawdown: number | null;
    is_sharpe_ratio: number | null;
    validation_badge: string | null;
    look_ahead_bias_check: boolean;
  };
  risk_result: {
    approved: boolean;
    risk_level: "LOW" | "MEDIUM" | "HIGH" | "BLOCKED" | (string & {});
    reasons: string[];
  };
  explanation: string;
  multi_agent_report: MultiAgentResearchReport | null;
  agent_reviews: AgentReviewBundle | null;
  executed: boolean;
  message: string;
  order: PaperOrder | null;
  run_steps?: RunStep[];
  case_id?: string;
  run_id?: string;
  market_provider?: string | null;
  execution_provider?: string | null;
  account_provider?: string | null;
};

export type RunCheckpoint = {
  checkpoint_id: string;
  run_id: string;
  step_id: string;
  step_label: string;
  status: string;
  input_snapshot: Record<string, unknown> | null;
  output_snapshot: Record<string, unknown> | null;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number;
};

// ── Portfolio ──────────────────────────────────────────────

export type WatchlistItem = {
  item_id: string;
  symbol: string;
  label: string | null;
  sector: string | null;
  industry: string | null;
  user_id: string;
  added_at: string;
  notes: string | null;
};

export type PortfolioHolding = {
  holding_id: string;
  symbol: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  sector: string | null;
  industry: string | null;
  weight: number;
};

export type PortfolioSummary = {
  total_market_value: number;
  total_cash: number;
  total_portfolio_value: number;
  total_unrealized_pnl: number;
  total_unrealized_pnl_pct: number;
  holdings: PortfolioHolding[];
  sector_breakdown: Record<string, number>;
  industry_breakdown: Record<string, number>;
  holding_count: number;
};

export type PortfolioDecision = {
  symbol: string;
  action: "buy" | "sell" | "hold" | "reduce" | (string & {});
  target_weight: number;
  rationale: string;
  confidence_score: number;
};

export type PortfolioManagerReport = {
  decisions: PortfolioDecision[];
  portfolio_context_summary: string;
  concentration_warnings: string[];
  sector_exposure_notes: string[];
  cash_ratio_note: string;
  overall_confidence: number;
};

export type RebalanceOrder = {
  symbol: string;
  side: string;
  quantity: number;
  estimated_amount: number;
  target_weight: number;
  current_weight: number;
  rationale: string;
};

export type RebalanceProposal = {
  orders: RebalanceOrder[];
  estimated_turnover: number;
  cash_after: number;
  rationale: string;
};

export type RebalanceRiskReview = {
  approved: boolean;
  risk_level: string;
  reasons: string[];
  flagged_orders: string[];
};

export type RebalanceWorkflowResult = {
  run_id: string;
  watchlist_symbols: string[];
  research_reports: Record<string, unknown>;
  portfolio_summary: PortfolioSummary | null;
  portfolio_manager_report: PortfolioManagerReport | null;
  rebalance_proposal: RebalanceProposal | null;
  risk_review: RebalanceRiskReview | null;
  executed_orders: Record<string, unknown>[];
  run_steps: Record<string, unknown>[];
  message: string;
};

// ── Investment Cases ──────────────────────────────────────

export type InvestmentCase = {
  case_id: string;
  symbol: string;
  thesis: string;
  confidence: number;
  risks: string[];
  data_sources: string[];
  decision: string;
  order_id: string | null;
  outcome: string | null;
  run_id: string | null;
  conversation_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ChatArtifactBase = {
  title: string;
};

export type ReactTraceArtifact = ChatArtifactBase & {
  type: "react_trace";
  payload: ReActResult;
};

export type ResearchReportArtifact = ChatArtifactBase & {
  type: "research_report";
  payload: ResearchReport;
};

export type MultiAgentArtifact = ChatArtifactBase & {
  type: "multi_agent_report";
  payload: MultiAgentResearchReport;
};

export type AutomationArtifact = ChatArtifactBase & {
  type: "automation_result";
  payload: AutomationResult;
};

export type PaperOrderArtifact = ChatArtifactBase & {
  type: "paper_order";
  payload: PaperOrder;
};

export type ChatArtifact =
  | ReactTraceArtifact
  | ResearchReportArtifact
  | MultiAgentArtifact
  | AutomationArtifact
  | PaperOrderArtifact;

export type ChatMessage = {
  message_id: string;
  conversation_id: string;
  role: "user" | "assistant";
  action: ReplyAction | null;
  content: string;
  artifacts: ChatArtifact[];
  status: "completed" | "error";
  created_at: string;
};

export type ConversationSummary = {
  conversation_id: string;
  title: string;
  symbol: string | null;
  llm_profile_id: string | null;
  strategy_name: StrategyName | null;
  market_provider: ProviderName | null;
  execution_provider: ProviderName | null;
  account_provider: ProviderName | null;
  user_id: string;
  message_count: number;
  created_at: string;
  updated_at: string;
};

export type ConversationDetail = ConversationSummary & {
  messages: ChatMessage[];
};

export type ReplyResponse = {
  conversation: ConversationSummary;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
};

export type PlanStepStatus = "pending" | "in_progress" | "completed" | "blocked" | "cancelled";

export type PlanStep = {
  id: string;
  text: string;
  status: PlanStepStatus;
};

export type AgentTaskStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "blocked"
  | "cancelled"
  | "failed";

export type AgentTask = {
  task_id: string;
  subject: string;
  description: string | null;
  status: AgentTaskStatus;
  blocked_by: string[];
  owner: string | null;
  linked_case_id: string | null;
  linked_run_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type BackgroundRunStatus = "pending" | "running" | "completed" | "failed";

export type BackgroundRun = {
  background_run_id: string;
  task_id: string | null;
  run_type: "automation" | (string & {});
  status: BackgroundRunStatus;
  input_payload: Record<string, unknown> | null;
  output_payload: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  automation_result?: AutomationResult | null;
};

export type ApprovalStatus = "pending" | "approved" | "rejected" | "expired";
export type ApprovalType =
  | "plan_approval"
  | "execution_approval"
  | "risk_exception"
  | "provider_health_override";

export type ApprovalRequest = {
  approval_id: string;
  request_type: ApprovalType;
  status: ApprovalStatus;
  subject: string;
  requested_by: string;
  target: string | null;
  linked_task_id: string | null;
  linked_run_id: string | null;
  payload: Record<string, unknown>;
  response: Record<string, unknown>;
  reason: string | null;
  expires_at: string | null;
  decided_at: string | null;
  created_at: string;
};
