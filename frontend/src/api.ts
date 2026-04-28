import type {
  AgentRun,
  AgentStatus,
  AutomationResult,
  LLMProfileListResponse,
  MemoryContext,
  MemoryRecord,
  MemoryStats,
  MultiAgentResearchReport,
  PaperOrder,
  Quote,
  ReActResult,
  ResearchReport,
  StrategyName
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers
    },
    ...options
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function fetchHealth(): Promise<{ status: string; service: string }> {
  return request("/api/v1/health");
}

export function fetchAgentStatus(): Promise<AgentStatus> {
  return request("/api/v1/agents/status");
}

export function fetchLLMProfiles(): Promise<LLMProfileListResponse> {
  return request("/api/v1/agents/llm-profiles");
}

export function fetchQuote(symbol: string): Promise<Quote> {
  return request(`/api/v1/market/quote/${symbol}`);
}

export async function fetchAgentRuns(limit = 8): Promise<AgentRun[]> {
  const payload = await request<{ runs: AgentRun[] }>(`/api/v1/agents/runs?limit=${limit}`);
  return payload.runs;
}

export async function fetchPaperOrders(limit = 8): Promise<PaperOrder[]> {
  const payload = await request<{ orders: PaperOrder[] }>(`/api/v1/orders/paper?limit=${limit}`);
  return payload.orders;
}

export function fetchMemoryContext(symbol: string, query?: string): Promise<MemoryContext> {
  const params = new URLSearchParams({ symbol });
  if (query?.trim()) {
    params.set("query", query.trim());
  }
  return request(`/api/v1/agents/memory/context?${params.toString()}`);
}

export function fetchRecentMemories(limit = 8): Promise<MemoryRecord[]> {
  return request(`/api/v1/agents/memory/recent?limit=${limit}`);
}

export function fetchMemoryStats(): Promise<MemoryStats> {
  return request("/api/v1/agents/memory/stats");
}

export function reloadMemoryIndex(): Promise<MemoryStats> {
  return request("/api/v1/agents/memory/reload-index", {
    method: "POST"
  });
}

export function compactMemory(symbol: string): Promise<MemoryRecord> {
  return request(`/api/v1/agents/memory/compact?symbol=${encodeURIComponent(symbol)}`, {
    method: "POST"
  });
}

export function runResearch(
  symbol: string,
  llmProfileId?: string | null
): Promise<ResearchReport> {
  return request("/api/v1/research/analyze", {
    method: "POST",
    body: JSON.stringify({ symbol, llm_profile_id: llmProfileId })
  });
}

export function runMultiAgentResearch(
  symbol: string,
  llmProfileId?: string | null
): Promise<MultiAgentResearchReport> {
  return request("/api/v1/agents/research/workflow", {
    method: "POST",
    body: JSON.stringify({ symbol, llm_profile_id: llmProfileId })
  });
}

export function runReActAgent(
  symbol: string,
  llmProfileId?: string | null
): Promise<ReActResult> {
  return request("/api/v1/agents/react/run", {
    method: "POST",
    body: JSON.stringify({ symbol, llm_profile_id: llmProfileId })
  });
}

export function runAutomation(
  symbol: string,
  mode: "manual" | "paper_auto",
  strategyName: StrategyName,
  llmProfileId?: string | null
): Promise<AutomationResult> {
  return request("/api/v1/automation/run", {
    method: "POST",
    body: JSON.stringify({
      symbol,
      mode,
      strategy_name: strategyName,
      llm_profile_id: llmProfileId
    })
  });
}
