import type {
  AgentRun,
  AgentStatus,
  AutomationResult,
  PaperOrder,
  Quote,
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

export function runResearch(symbol: string): Promise<ResearchReport> {
  return request("/api/v1/research/analyze", {
    method: "POST",
    body: JSON.stringify({ symbol })
  });
}

export function runAutomation(
  symbol: string,
  mode: "manual" | "paper_auto",
  strategyName: StrategyName
): Promise<AutomationResult> {
  return request("/api/v1/automation/run", {
    method: "POST",
    body: JSON.stringify({
      symbol,
      mode,
      strategy_name: strategyName
    })
  });
}
