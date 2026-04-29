import type {
  AgentRun,
  AgentStatus,
  ConversationDetail,
  ConversationSummary,
  LLMProfileListResponse,
  MemoryContext,
  MemoryRecord,
  MemoryStats,
  PaperOrder,
  ReplyAction,
  ReplyResponse,
  StrategyName
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
  }
};

export const ordersApi = {
  async fetchPaperOrders(limit = 8): Promise<PaperOrder[]> {
    const payload = await requestJson<{ orders: PaperOrder[] }>(`/api/v1/orders/paper?limit=${limit}`);
    return payload.orders;
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
    },
    signal?: AbortSignal
  ): Promise<ReplyResponse> {
    return postJson(`/api/v1/chat/conversations/${conversationId}/reply`, input, signal);
  }
};
