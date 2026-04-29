import { useCallback, useEffect, useMemo, useState } from "react";
import { agentsApi, ApiError, chatApi, ordersApi, statusApi } from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { RightRail } from "./components/RightRail";
import { Sidebar } from "./components/Sidebar";
import type {
  AgentRun,
  AgentStatus,
  ChatMessage,
  ConversationDetail,
  ConversationSummary,
  LLMProfileListResponse,
  PaperOrder,
  ReplyAction,
  StrategyName
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
};

const DEFAULT_SYMBOL = "AAPL";
const DEFAULT_STRATEGY: StrategyName = "moving_average_cross";
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
      profiles: null
    }
  });
  const [activity, setActivity] = useState<AsyncState<{ runs: AgentRun[]; orders: PaperOrder[] }>>({
    loading: true,
    error: null,
    data: { runs: [], orders: [] }
  });
  const [composerText, setComposerText] = useState("");
  const [selectedAction, setSelectedAction] = useState<ReplyAction>("chat");
  const [contextDraft, setContextDraft] = useState({
    title: "",
    symbol: DEFAULT_SYMBOL,
    llmProfileId: "",
    strategyName: DEFAULT_STRATEGY as StrategyName
  });

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
      {
        label: "Strategy",
        value: contextDraft.strategyName === "valuation_band" ? "Valuation Band" : "Moving Average"
      }
    ],
    [activeProfile?.label, contextDraft.strategyName, contextDraft.symbol]
  );

  const loadSidebarStatus = useCallback(async () => {
    setSidebarStatus((current) => ({ ...current, loading: true, error: null }));
    try {
      const health = await statusApi.fetchHealth();
      const agentStatus = await agentsApi.fetchStatus();
      const profilesPayload = await agentsApi.fetchProfiles();
      setSidebarStatus({
        loading: false,
        error: null,
        data: {
          health: `${health.status} / ${health.service}`,
          agentStatus,
          profiles: profilesPayload
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
      const runs = await agentsApi.fetchRuns(6);
      const orders = await ordersApi.fetchPaperOrders(6);
      setActivity({
        loading: false,
        error: null,
        data: { runs, orders }
      });
    } catch (error) {
      setActivity((current) => ({
        ...current,
        loading: false,
        error: getErrorMessage(error)
      }));
    }
  }, []);

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
          strategy_name: DEFAULT_STRATEGY
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
    void Promise.allSettled([loadSidebarStatus(), loadActivity(), ensureConversation()]);
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
      strategyName: activeConversation.data.strategy_name ?? DEFAULT_STRATEGY
    });
  }, [activeConversation.data]);

  const handleCreateConversation = useCallback(async () => {
    try {
      const created = await chatApi.createConversation({
        symbol: contextDraft.symbol || DEFAULT_SYMBOL,
        llm_profile_id: activeProfileId || null,
        strategy_name: contextDraft.strategyName || DEFAULT_STRATEGY
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
        strategy_name: contextDraft.strategyName
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
        strategy_name: contextDraft.strategyName
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
        latestRun={latestRun}
        latestOrder={latestOrder}
        onContextDraftChange={handleContextDraftChange}
        onSaveContext={handleSaveContext}
        onRefreshStatus={loadSidebarStatus}
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
