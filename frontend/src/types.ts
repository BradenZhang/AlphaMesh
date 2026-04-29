export type AgentStatus = {
  provider: "openai" | "anthropic" | "gemini" | "mock" | (string & {});
  model: string;
  is_mock: boolean;
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
};

export type ResearchReport = {
  symbol: string;
  summary: string;
  key_metrics: Record<string, number | string>;
  valuation_view: string;
  risks: string[];
  confidence_score: number;
};

export type AgentFinding = {
  agent_name: string;
  symbol: string;
  thesis: string;
  key_points: string[];
  metrics: Record<string, number | string>;
  risks: string[];
  confidence_score: number;
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
