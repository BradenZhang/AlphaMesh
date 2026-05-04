import type {
  AgentRun,
  AgentStatus,
  AgentTask,
  ApprovalRequest,
  ApprovalType,
  BackgroundRun,
  ConversationDetail,
  ConversationSummary,
  InvestmentCase,
  LLMCall,
  LLMProfileListResponse,
  MemoryContext,
  MemoryRecord,
  MemoryStats,
  PaperOrder,
  PortfolioHolding,
  PortfolioSummary,
  ProviderHealth,
  RebalanceWorkflowResult,
  ReplyAction,
  ReplyResponse,
  ProviderName,
  StrategyName,
  WatchlistItem
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const DEFAULT_TIMEOUT_MS = 30_000;

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function requestJson<T>(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...fetchInit } = init ?? {};

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  // Merge caller signal with our timeout controller
  if (fetchInit.signal) {
    fetchInit.signal.addEventListener("abort", () => controller.abort());
  }

  try {
    const headers: Record<string, string> = { ...fetchInit.headers as Record<string, string> };
    if (fetchInit.body) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...fetchInit,
      headers,
      signal: controller.signal,
    });

    const contentType = response.headers.get("content-type") ?? "";
    const isJson = contentType.includes("application/json");
    const payload = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      const detail =
        typeof payload === "string"
          ? payload
          : typeof payload?.detail === "string"
            ? payload.detail
            : Array.isArray(payload?.detail)
              ? payload.detail.map((d: { msg?: string }) => d.msg || String(d)).join("; ")
              : `Request failed with ${response.status}`;
      throw new ApiError(response.status, detail);
    }

    return payload as T;
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, `Request timed out after ${timeoutMs}ms`);
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

function postJson<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });
}

function patchJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return requestJson<T>(path, {
    method: "PATCH",
    body: JSON.stringify(body),
    signal,
  });
}

export const statusApi = {
  fetchHealth(): Promise<{ status: string; service: string }> {
    return requestJson("/api/v1/health");
  }
};

export const agentsApi = {
  fetchStatus(): Promise<AgentStatus> {
    return requestJson("/api/v1/agents/status");
  },
  fetchProfiles(): Promise<LLMProfileListResponse> {
    return requestJson("/api/v1/agents/llm-profiles");
  },
  async fetchRuns(limit = 8): Promise<AgentRun[]> {
    const payload = await requestJson<{ runs: AgentRun[] }>(`/api/v1/agents/runs?limit=${limit}`);
    return payload.runs;
  },
  async fetchLLMCalls(limit = 20): Promise<LLMCall[]> {
    const payload = await requestJson<{ calls: LLMCall[] }>(`/api/v1/agents/llm-calls?limit=${limit}`);
    return payload.calls;
  },
  async fetchProviderHealth(): Promise<ProviderHealth[]> {
    const payload = await requestJson<{ providers: ProviderHealth[] }>("/api/v1/agents/providers/health");
    return payload.providers;
  }
};

export const ordersApi = {
  async fetchPaperOrders(limit = 8): Promise<PaperOrder[]> {
    const payload = await requestJson<{ orders: PaperOrder[] }>(`/api/v1/orders/paper?limit=${limit}`);
    return payload.orders;
  }
};

export const automationApi = {
  retry(runId: string): Promise<unknown> {
    return postJson(`/api/v1/automation/retry/${runId}`);
  },
  replay(runId: string): Promise<unknown> {
    return postJson(`/api/v1/automation/replay/${runId}`);
  },
  async getCheckpoints(runId: string): Promise<import("./types").RunCheckpoint[]> {
    const payload = await requestJson<{ checkpoints: import("./types").RunCheckpoint[] }>(`/api/v1/automation/checkpoints/${runId}`);
    return payload.checkpoints;
  }
};

export const casesApi = {
  async listCases(symbol?: string, limit = 20): Promise<InvestmentCase[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (symbol) params.set("symbol", symbol);
    const payload = await requestJson<{ cases: InvestmentCase[] }>(`/api/v1/cases?${params.toString()}`);
    return payload.cases;
  },
  getCase(caseId: string): Promise<InvestmentCase> {
    return requestJson(`/api/v1/cases/${caseId}`);
  },
  updateOutcome(caseId: string, outcome: string): Promise<InvestmentCase> {
    return patchJson(`/api/v1/cases/${caseId}`, { outcome });
  }
};

export const memoryApi = {
  fetchContext(symbol: string, query?: string): Promise<MemoryContext> {
    const params = new URLSearchParams({ symbol });
    if (query?.trim()) {
      params.set("query", query.trim());
    }
    return requestJson(`/api/v1/agents/memory/context?${params.toString()}`);
  },
  fetchRecent(limit = 8): Promise<MemoryRecord[]> {
    return requestJson(`/api/v1/agents/memory/recent?limit=${limit}`);
  },
  fetchStats(): Promise<MemoryStats> {
    return requestJson("/api/v1/agents/memory/stats");
  }
};

export const chatApi = {
  async listConversations(): Promise<ConversationSummary[]> {
    const payload = await requestJson<{ conversations: ConversationSummary[] }>("/api/v1/chat/conversations");
    return payload.conversations;
  },
  createConversation(input?: {
    symbol?: string;
    llm_profile_id?: string | null;
    strategy_name?: StrategyName | null;
    market_provider?: ProviderName | null;
    execution_provider?: ProviderName | null;
    account_provider?: ProviderName | null;
  }): Promise<ConversationSummary> {
    return postJson("/api/v1/chat/conversations", input ?? {});
  },
  getConversation(conversationId: string): Promise<ConversationDetail> {
    return requestJson(`/api/v1/chat/conversations/${conversationId}`);
  },
  updateConversation(
    conversationId: string,
    input: {
      title?: string;
      symbol?: string | null;
      llm_profile_id?: string | null;
      strategy_name?: StrategyName | null;
      market_provider?: ProviderName | null;
      execution_provider?: ProviderName | null;
      account_provider?: ProviderName | null;
    }
  ): Promise<ConversationSummary> {
    return patchJson(`/api/v1/chat/conversations/${conversationId}`, input);
  },
  reply(
    conversationId: string,
    input: {
      message: string;
      action: ReplyAction;
      symbol?: string | null;
      llm_profile_id?: string | null;
      strategy_name?: StrategyName | null;
      market_provider?: ProviderName | null;
      execution_provider?: ProviderName | null;
      account_provider?: ProviderName | null;
    },
    signal?: AbortSignal
  ): Promise<ReplyResponse> {
    return postJson(`/api/v1/chat/conversations/${conversationId}/reply`, input, signal);
  }
};

export const portfolioApi = {
  async listWatchlist(): Promise<WatchlistItem[]> {
    const payload = await requestJson<{ items: WatchlistItem[] }>("/api/v1/portfolio/watchlist");
    return payload.items;
  },
  addToWatchlist(input: {
    symbol: string;
    label?: string;
    sector?: string;
    industry?: string;
    notes?: string;
  }): Promise<WatchlistItem> {
    return postJson("/api/v1/portfolio/watchlist", input);
  },
  removeFromWatchlist(itemId: string): Promise<{ ok: boolean }> {
    return requestJson(`/api/v1/portfolio/watchlist/${itemId}`, { method: "DELETE" });
  },
  getPortfolioSummary(): Promise<PortfolioSummary> {
    return requestJson("/api/v1/portfolio/summary");
  },
  async listHoldings(): Promise<PortfolioHolding[]> {
    return requestJson("/api/v1/portfolio/holdings");
  },
  runRebalance(input?: {
    user_id?: string;
    max_orders?: number;
    force?: boolean;
  }): Promise<RebalanceWorkflowResult> {
    return postJson("/api/v1/portfolio/rebalance/run", input ?? {});
  },
  batchResearch(): Promise<Record<string, unknown>> {
    return postJson("/api/v1/portfolio/watchlist/research");
  }
};

export const harnessApi = {
  async listTasks(input?: { status?: string; ready?: boolean }): Promise<AgentTask[]> {
    const params = new URLSearchParams();
    if (input?.status) params.set("status", input.status);
    if (input?.ready !== undefined) params.set("ready", String(input.ready));
    const suffix = params.toString() ? `?${params.toString()}` : "";
    const payload = await requestJson<{ tasks: AgentTask[] }>(`/api/v1/tasks/${suffix}`);
    return payload.tasks;
  },
  createTask(input: {
    subject: string;
    description?: string;
    blocked_by?: string[];
    owner?: string;
    linked_case_id?: string;
    linked_run_id?: string;
    metadata?: Record<string, unknown>;
  }): Promise<AgentTask> {
    return postJson("/api/v1/tasks/", input);
  },
  updateTask(taskId: string, input: Partial<AgentTask>): Promise<AgentTask> {
    return patchJson(`/api/v1/tasks/${taskId}`, input);
  },
  startAutomationTask(
    taskId: string,
    automationRequest: Record<string, unknown>
  ): Promise<BackgroundRun> {
    return postJson(`/api/v1/tasks/${taskId}/start`, {
      run_type: "automation",
      automation_request: automationRequest,
    });
  },
  getBackgroundRun(backgroundRunId: string): Promise<BackgroundRun> {
    return requestJson(`/api/v1/tasks/background-runs/${backgroundRunId}`);
  },
  async listApprovals(status?: string): Promise<ApprovalRequest[]> {
    const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
    const payload = await requestJson<{ approvals: ApprovalRequest[] }>(
      `/api/v1/approvals/${suffix}`
    );
    return payload.approvals;
  },
  createApproval(input: {
    request_type: ApprovalType;
    subject: string;
    requested_by?: string;
    target?: string;
    linked_task_id?: string;
    linked_run_id?: string;
    payload?: Record<string, unknown>;
    expires_at?: string;
  }): Promise<ApprovalRequest> {
    return postJson("/api/v1/approvals/", input);
  },
  respondApproval(
    approvalId: string,
    input: { approve: boolean; reason?: string; response?: Record<string, unknown> }
  ): Promise<ApprovalRequest> {
    return postJson(`/api/v1/approvals/${approvalId}/respond`, input);
  },
};
