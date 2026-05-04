import { useCallback, useEffect, useMemo, useState } from "react";
import { agentsApi, ApiError, automationApi, casesApi, chatApi, ordersApi, portfolioApi, statusApi } from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { renderArtifactBody } from "./components/MessageBubble";
import { RebalanceDrawer } from "./components/RebalanceDrawer";
import { RightRail } from "./components/RightRail";
import { RunDetailDrawer } from "./components/RunDetailDrawer";
import { Sidebar } from "./components/Sidebar";
import type {
  AgentRun,
  AgentStatus,
  ChatArtifact,
  ChatMessage,
  ConversationDetail,
  ConversationSummary,
  InvestmentCase,
  LLMCall,
  LLMProfileListResponse,
  PaperOrder,
  PortfolioSummary,
  ProviderHealth,
  ProviderName,
  RebalanceWorkflowResult,
  ReplyAction,
  StrategyName,
  WatchlistItem
} from "./types";
import { getErrorMessage } from "./utils/format";

type AsyncState<T> = {
  loading: boolean;
  error: string | null;
  data: T;
};

type SidebarStatus = {
  health: string;
  agentStatus: AgentStatus | null;
  profiles: LLMProfileListResponse | null;
  providerHealth: ProviderHealth[];
};

const DEFAULT_SYMBOL = "AAPL";
const DEFAULT_STRATEGY: StrategyName = "moving_average_cross";
const DEFAULT_PROVIDER: ProviderName = "mock";
const EMPTY_MESSAGES: ChatMessage[] = [];

function makePendingMessage(
  conversationId: string,
  role: "user" | "assistant",
  content: string,
  action: ReplyAction | null,
  status: "completed" | "error" = "completed"
): ChatMessage {
  return {
    message_id: `pending-${role}-${crypto.randomUUID()}`,
    conversation_id: conversationId,
    role,
    action,
    content,
    artifacts: [],
    status,
    created_at: new Date().toISOString()
  };
}

export default function App() {
  const [conversationList, setConversationList] = useState<AsyncState<ConversationSummary[]>>({
    loading: true,
    error: null,
    data: []
  });
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [activeConversation, setActiveConversation] = useState<AsyncState<ConversationDetail | null>>({
    loading: false,
    error: null,
    data: null
  });
  const [replyPending, setReplyPending] = useState<{ active: boolean; error: string | null }>({
    active: false,
    error: null
  });
  const [sidebarStatus, setSidebarStatus] = useState<AsyncState<SidebarStatus>>({
    loading: true,
    error: null,
    data: {
      health: "checking",
      agentStatus: null,
      profiles: null,
      providerHealth: []
    }
  });
  const [activity, setActivity] = useState<AsyncState<{ runs: AgentRun[]; orders: PaperOrder[]; llmCalls: LLMCall[]; cases: InvestmentCase[] }>>({
    loading: true,
    error: null,
    data: { runs: [], orders: [], llmCalls: [], cases: [] }
  });
  const [composerText, setComposerText] = useState("");
  const [selectedAction, setSelectedAction] = useState<ReplyAction>("chat");
  const [contextDraft, setContextDraft] = useState({
    title: "",
    symbol: DEFAULT_SYMBOL,
    llmProfileId: "",
    strategyName: DEFAULT_STRATEGY as StrategyName,
    marketProvider: DEFAULT_PROVIDER as ProviderName,
    executionProvider: DEFAULT_PROVIDER as ProviderName,
    accountProvider: DEFAULT_PROVIDER as ProviderName
  });
  const [drawerState, setDrawerState] = useState<{
    open: boolean;
    title: string;
    artifact: ChatArtifact | null;
  }>({ open: false, title: "", artifact: null });
  const [retrying, setRetrying] = useState(false);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [portfolioSummary, setPortfolioSummary] = useState<PortfolioSummary | null>(null);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [rebalanceResult, setRebalanceResult] = useState<RebalanceWorkflowResult | null>(null);
  const [rebalanceDrawerOpen, setRebalanceDrawerOpen] = useState(false);

  const profiles = sidebarStatus.data.profiles?.profiles ?? [];
  const activeProfileId =
    contextDraft.llmProfileId || sidebarStatus.data.profiles?.default_profile_id || "";
  const activeProfile =
    profiles.find((profile) => profile.id === activeProfileId) ?? null;
  const canSend = Boolean(activeConversationId && composerText.trim()) && !replyPending.active;
  const latestRun = activity.data.runs[0] ?? null;
  const latestOrder = activity.data.orders[0] ?? null;

  const contextChips = useMemo(
    () => [
      { label: "Symbol", value: contextDraft.symbol || DEFAULT_SYMBOL },
      { label: "Profile", value: activeProfile?.label ?? "Default" },
      { label: "Market", value: contextDraft.marketProvider },
      {
        label: "Strategy",
        value: contextDraft.strategyName === "valuation_band" ? "Valuation Band" : "Moving Average"
      }
    ],
    [activeProfile?.label, contextDraft.marketProvider, contextDraft.strategyName, contextDraft.symbol]
  );

  const loadSidebarStatus = useCallback(async () => {
    setSidebarStatus((current) => ({ ...current, loading: true, error: null }));
    try {
      const health = await statusApi.fetchHealth();
      const agentStatus = await agentsApi.fetchStatus();
      const profilesPayload = await agentsApi.fetchProfiles();
      const providerHealth = await agentsApi.fetchProviderHealth();
      setSidebarStatus({
        loading: false,
        error: null,
        data: {
          health: `${health.status} / ${health.service}`,
          agentStatus,
          profiles: profilesPayload,
          providerHealth
        }
      });
    } catch (error) {
      setSidebarStatus((current) => ({
        ...current,
        loading: false,
        error: getErrorMessage(error)
      }));
    }
  }, []);

  const loadActivity = useCallback(async () => {
    setActivity((current) => ({ ...current, loading: true, error: null }));
    try {
      const [runs, orders, llmCalls, cases] = await Promise.all([
        agentsApi.fetchRuns(6),
        ordersApi.fetchPaperOrders(6),
        agentsApi.fetchLLMCalls(20),
        casesApi.listCases(undefined, 8)
      ]);
      setActivity({
        loading: false,
        error: null,
        data: { runs, orders, llmCalls, cases }
      });
    } catch (error) {
      setActivity((current) => ({
        ...current,
        loading: false,
        error: getErrorMessage(error)
      }));
    }
  }, []);

  const loadPortfolio = useCallback(async () => {
    setPortfolioLoading(true);
    try {
      const [items, summary] = await Promise.all([
        portfolioApi.listWatchlist(),
        portfolioApi.getPortfolioSummary()
      ]);
      setWatchlist(items);
      setPortfolioSummary(summary);
    } catch {
      // silent — portfolio is optional context
    } finally {
      setPortfolioLoading(false);
    }
  }, []);

  const handleAddWatchlist = useCallback(async (symbol: string) => {
    try {
      await portfolioApi.addToWatchlist({ symbol });
      await loadPortfolio();
    } catch {
      // duplicate or API error — ignore for MVP
    }
  }, [loadPortfolio]);

  const handleRemoveWatchlist = useCallback(async (itemId: string) => {
    try {
      await portfolioApi.removeFromWatchlist(itemId);
      await loadPortfolio();
    } catch {
      // ignore for MVP
    }
  }, [loadPortfolio]);

  const handleBatchResearch = useCallback(async () => {
    setPortfolioLoading(true);
    try {
      await portfolioApi.batchResearch();
      await loadPortfolio();
    } catch {
      // ignore for MVP
    } finally {
      setPortfolioLoading(false);
    }
  }, [loadPortfolio]);

  const handleRebalance = useCallback(async () => {
    setPortfolioLoading(true);
    try {
      const result = await portfolioApi.runRebalance();
      setRebalanceResult(result);
      setRebalanceDrawerOpen(true);
      await loadPortfolio();
    } catch {
      // ignore for MVP
    } finally {
      setPortfolioLoading(false);
    }
  }, [loadPortfolio]);

  const loadConversation = useCallback(async (conversationId: string) => {
    let cancelled = false;
    setActiveConversation((current) => ({ ...current, loading: true, error: null }));
    try {
      const conversation = await chatApi.getConversation(conversationId);
      if (!cancelled) {
        setActiveConversation({
          loading: false,
          error: null,
          data: conversation
        });
      }
    } catch (error) {
      if (!cancelled) {
        setActiveConversation({
          loading: false,
          error: getErrorMessage(error),
          data: null
        });
      }
    }
    return () => { cancelled = true; };
  }, []);

  const ensureConversation = useCallback(async () => {
    setConversationList((current) => ({ ...current, loading: true, error: null }));
    try {
      const conversations = await chatApi.listConversations();
      if (conversations.length === 0) {
        const created = await chatApi.createConversation({
          symbol: DEFAULT_SYMBOL,
          strategy_name: DEFAULT_STRATEGY,
          market_provider: DEFAULT_PROVIDER,
          execution_provider: DEFAULT_PROVIDER,
          account_provider: DEFAULT_PROVIDER
        });
        setConversationList({
          loading: false,
          error: null,
          data: [created]
        });
        setActiveConversationId(created.conversation_id);
        return;
      }
      setConversationList({
        loading: false,
        error: null,
        data: conversations
      });
      setActiveConversationId((current) => current ?? conversations[0].conversation_id);
    } catch (error) {
      setConversationList({
        loading: false,
        error: getErrorMessage(error),
        data: []
      });
    }
  }, []);

  useEffect(() => {
    void Promise.allSettled([loadSidebarStatus(), loadActivity(), ensureConversation(), loadPortfolio()]);
  }, [loadSidebarStatus, loadActivity, ensureConversation]);

  useEffect(() => {
    if (!activeConversationId) return;
    void loadConversation(activeConversationId);
  }, [activeConversationId, loadConversation]);

  useEffect(() => {
    if (!activeConversation.data) return;
      setContextDraft({
        title: activeConversation.data.title,
        symbol: activeConversation.data.symbol ?? DEFAULT_SYMBOL,
        llmProfileId: activeConversation.data.llm_profile_id ?? "",
        strategyName: activeConversation.data.strategy_name ?? DEFAULT_STRATEGY,
        marketProvider: activeConversation.data.market_provider ?? DEFAULT_PROVIDER,
        executionProvider: activeConversation.data.execution_provider ?? DEFAULT_PROVIDER,
        accountProvider: activeConversation.data.account_provider ?? DEFAULT_PROVIDER
      });
  }, [activeConversation.data]);

  const handleCreateConversation = useCallback(async () => {
    try {
      const created = await chatApi.createConversation({
        symbol: contextDraft.symbol || DEFAULT_SYMBOL,
        llm_profile_id: activeProfileId || null,
        strategy_name: contextDraft.strategyName || DEFAULT_STRATEGY,
        market_provider: contextDraft.marketProvider,
        execution_provider: contextDraft.executionProvider,
        account_provider: contextDraft.accountProvider
      });
      setConversationList((current) => ({
        loading: false,
        error: null,
        data: [created, ...current.data]
      }));
      setActiveConversationId(created.conversation_id);
      setComposerText("");
      setSelectedAction("chat");
    } catch (error) {
      setConversationList((current) => ({
        ...current,
        error: getErrorMessage(error)
      }));
    }
  }, [contextDraft.symbol, contextDraft.strategyName, activeProfileId]);

  const handleSaveContext = useCallback(async () => {
    if (!activeConversationId) return;
    try {
      const updated = await chatApi.updateConversation(activeConversationId, {
        title: contextDraft.title.trim() || "New Chat",
        symbol: contextDraft.symbol.trim().toUpperCase() || DEFAULT_SYMBOL,
        llm_profile_id: activeProfileId || null,
        strategy_name: contextDraft.strategyName,
        market_provider: contextDraft.marketProvider,
        execution_provider: contextDraft.executionProvider,
        account_provider: contextDraft.accountProvider
      });
      setConversationList((current) => ({
        loading: false,
        error: null,
        data: current.data.map((conversation) =>
          conversation.conversation_id === updated.conversation_id ? updated : conversation
        )
      }));
      setActiveConversation((current) => ({
        loading: false,
        error: null,
        data: current.data
          ? { ...current.data, ...updated }
          : current.data
      }));
    } catch (error) {
      setReplyPending({ active: false, error: getErrorMessage(error) });
    }
  }, [activeConversationId, activeProfileId, contextDraft]);

  const handleSend = useCallback(async () => {
    if (!activeConversationId || !composerText.trim()) return;

    const message = composerText.trim();
    const action = selectedAction;
    const pendingUser = makePendingMessage(activeConversationId, "user", message, action);
    const pendingAssistant = makePendingMessage(
      activeConversationId,
      "assistant",
      `Running ${action.replaceAll("_", " ")}...`,
      action
    );

    setReplyPending({ active: true, error: null });
    setComposerText("");
    setSelectedAction("chat");
    setActiveConversation((current) => {
      if (!current.data) return current;
      return {
        loading: false,
        error: null,
        data: {
          ...current.data,
          messages: [...current.data.messages, pendingUser, pendingAssistant]
        }
      };
    });

    try {
      const reply = await chatApi.reply(activeConversationId, {
        message,
        action,
        symbol: contextDraft.symbol.trim().toUpperCase() || DEFAULT_SYMBOL,
        llm_profile_id: activeProfileId || null,
        strategy_name: contextDraft.strategyName,
        market_provider: contextDraft.marketProvider,
        execution_provider: contextDraft.executionProvider,
        account_provider: contextDraft.accountProvider
      });
      setActiveConversation((current) => {
        if (!current.data) return current;
        const committedMessages = current.data.messages.filter(
          (item) => !item.message_id.startsWith("pending-")
        );
        return {
          loading: false,
          error: null,
          data: {
            ...current.data,
            ...reply.conversation,
            messages: [...committedMessages, reply.user_message, reply.assistant_message]
          }
        };
      });
      setConversationList((current) => ({
        loading: false,
        error: null,
        data: upsertConversation(current.data, reply.conversation)
      }));
      await Promise.allSettled([loadActivity(), loadSidebarStatus()]);
      setReplyPending({ active: false, error: null });
    } catch (error) {
      const detail = getErrorMessage(error);
      setActiveConversation((current) => {
        if (!current.data) return current;
        const nextMessages = [...current.data.messages];
        const lastMessage = nextMessages.at(-1);
        if (lastMessage?.message_id.startsWith("pending-assistant")) {
          nextMessages[nextMessages.length - 1] = { ...lastMessage, content: detail, status: "error" };
        }
        return { loading: false, error: detail, data: { ...current.data, messages: nextMessages } };
      });
      await Promise.allSettled([loadConversation(activeConversationId), loadActivity()]);
      setReplyPending({ active: false, error: detail });
    }
  }, [activeConversationId, composerText, selectedAction, contextDraft, activeProfileId, loadActivity, loadSidebarStatus, loadConversation]);

  const handleContextDraftChange = useCallback((update: Partial<typeof contextDraft>) => {
    setContextDraft((current) => ({ ...current, ...update }));
  }, []);

  const handleArtifactOpen = useCallback((artifact: ChatArtifact) => {
    setDrawerState({ open: true, title: artifact.title, artifact });
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setDrawerState((current) => ({ ...current, open: false }));
  }, []);

  const handleRetry = useCallback(async () => {
    const artifact = drawerState.artifact;
    if (!artifact || artifact.type !== "automation_result") return;
    const runId = artifact.payload.run_id;
    if (!runId) return;
    setRetrying(true);
    try {
      await automationApi.retry(runId);
      await loadActivity();
      if (activeConversationId) await loadConversation(activeConversationId);
    } catch {
      // errors are shown in the refreshed conversation
    } finally {
      setRetrying(false);
    }
  }, [drawerState.artifact, activeConversationId, loadActivity, loadConversation]);

  const threadMessages = activeConversation.data?.messages ?? EMPTY_MESSAGES;

  return (
    <div className="workspaceShell">
      <Sidebar
        conversationList={conversationList.data}
        activeConversationId={activeConversationId}
        conversationListError={conversationList.error}
        onSelectConversation={setActiveConversationId}
        onCreateConversation={handleCreateConversation}
      />

      <ChatPanel
        conversation={activeConversation.data}
        conversationLoading={activeConversation.loading}
        conversationError={activeConversation.error}
        threadMessages={threadMessages}
        composerText={composerText}
        selectedAction={selectedAction}
        replyPending={replyPending.active}
        replyError={replyPending.error}
        contextChips={contextChips}
        canSend={canSend}
        onComposerTextChange={setComposerText}
        onSelectedActionChange={setSelectedAction}
        onSend={handleSend}
        onArtifactOpen={handleArtifactOpen}
      />

      <RightRail
        contextDraft={contextDraft}
        profiles={profiles}
        activeProfileId={activeProfileId}
        sidebarStatus={sidebarStatus.data}
        sidebarError={sidebarStatus.error}
        activityRuns={activity.data.runs}
        activityOrders={activity.data.orders}
        activityError={activity.error}
        llmCalls={activity.data.llmCalls}
        cases={activity.data.cases}
        latestRun={latestRun}
        latestOrder={latestOrder}
        watchlist={watchlist}
        portfolioSummary={portfolioSummary}
        portfolioLoading={portfolioLoading}
        onContextDraftChange={handleContextDraftChange}
        onSaveContext={handleSaveContext}
        onRefreshStatus={loadSidebarStatus}
        onAddWatchlist={handleAddWatchlist}
        onRemoveWatchlist={handleRemoveWatchlist}
        onBatchResearch={handleBatchResearch}
        onRebalance={handleRebalance}
      />

      <RunDetailDrawer
        open={drawerState.open}
        title={drawerState.title}
        onClose={handleCloseDrawer}
      >
        {drawerState.artifact ? renderArtifactBody(drawerState.artifact, handleRetry) : null}
      </RunDetailDrawer>

      <RebalanceDrawer
        open={rebalanceDrawerOpen}
        result={rebalanceResult}
        onClose={() => setRebalanceDrawerOpen(false)}
      />
    </div>
  );
}

function upsertConversation(
  conversations: ConversationSummary[],
  nextConversation: ConversationSummary
): ConversationSummary[] {
  const filtered = conversations.filter(
    (conversation) => conversation.conversation_id !== nextConversation.conversation_id
  );
  return [nextConversation, ...filtered];
}
