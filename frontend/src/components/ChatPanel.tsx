import { useEffect, useRef } from "react";
import type { ChatArtifact, ChatMessage, ConversationDetail, ReplyAction, StrategyName } from "../types";
import { MessageBubble } from "./MessageBubble";

const DEFAULT_SYMBOL = "AAPL";

const QUICK_ACTIONS: Array<{ id: ReplyAction; label: string; hint: string }> = [
  { id: "chat", label: "Chat", hint: "Natural language with ReAct" },
  { id: "research", label: "Research", hint: "Full committee pass" },
  { id: "manual_plan", label: "Manual Plan", hint: "No order submission" },
  { id: "paper_auto", label: "Paper Auto", hint: "Submit mock paper order" }
];

const STARTER_PROMPTS: Array<{ title: string; body: string; action: ReplyAction }> = [
  {
    title: "Earnings breakdown",
    body: "Summarize the latest quarter, isolate the main drivers, and call out guidance changes.",
    action: "chat"
  },
  {
    title: "Committee research pass",
    body: "Run the full multi-agent research workflow and return the committee view with key risks.",
    action: "research"
  },
  {
    title: "Manual plan",
    body: "Build a trading plan with backtest, risk review, and execution recommendation without placing orders.",
    action: "manual_plan"
  }
];

interface ChatPanelProps {
  conversation: ConversationDetail | null;
  conversationLoading: boolean;
  conversationError: string | null;
  threadMessages: ChatMessage[];
  composerText: string;
  selectedAction: ReplyAction;
  replyPending: boolean;
  replyError: string | null;
  contextChips: Array<{ label: string; value: string }>;
  canSend: boolean;
  onComposerTextChange: (text: string) => void;
  onSelectedActionChange: (action: ReplyAction) => void;
  onSend: () => void;
  onArtifactOpen?: (artifact: ChatArtifact) => void;
}

export function ChatPanel({
  conversation,
  conversationLoading,
  conversationError,
  threadMessages,
  composerText,
  selectedAction,
  replyPending,
  replyError,
  contextChips,
  canSend,
  onComposerTextChange,
  onSelectedActionChange,
  onSend,
  onArtifactOpen
}: ChatPanelProps) {
  const threadRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    const el = threadRef.current;
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [threadMessages.length]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) onSend();
    }
  };

  return (
    <main className="chatPanel">
      <header className="chatHeader">
        <div className="headerTitleGroup">
          <p className="eyebrow">Live Thread</p>
          <h2>{conversation?.title ?? "Loading conversation"}</h2>
          <p className="headerSubline">
            Conversation-first research workspace for market questions, automation plans, and paper
            execution.
          </p>
        </div>
        <div className="headerMeta">
          {contextChips.map((chip) => (
            <span className="infoChip" key={chip.label}>
              {chip.label}: {chip.value}
            </span>
          ))}
        </div>
      </header>

      <section className="messageThread" ref={threadRef}>
        {conversationLoading ? <ThreadNotice text="Loading conversation..." /> : null}
        {conversationError ? <ThreadNotice error text={conversationError} /> : null}
        {threadMessages.length === 0 && !conversationLoading ? (
          <div className="emptyThread">
            <div className="emptyThreadIntro">
              <strong>Start with a question, a research pass, or an execution workflow.</strong>
              <p>
                Default send uses ReAct. Switch the mode when you need the full committee path or
                a manual or paper automation run.
              </p>
            </div>
            <div className="promptGrid">
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  className="promptCard"
                  key={prompt.title}
                  onClick={() => {
                    onComposerTextChange(prompt.body);
                    onSelectedActionChange(prompt.action);
                  }}
                  type="button"
                >
                  <strong>{prompt.title}</strong>
                  <span>{prompt.body}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}
        {threadMessages.map((message) => (
          <MessageBubble
            key={message.message_id}
            message={message}
            onArtifactOpen={onArtifactOpen}
          />
        ))}
      </section>

      <footer className="composerPanel">
        <div className="actionBar">
          {QUICK_ACTIONS.map((action) => (
            <button
              className={`actionPill ${selectedAction === action.id ? "active" : ""}`}
              key={action.id}
              onClick={() => onSelectedActionChange(action.id)}
              type="button"
            >
              <strong>{action.label}</strong>
              <small>{action.hint}</small>
            </button>
          ))}
        </div>
        <div className="composerCard">
          <div className="composerFrame">
            <span className="composerLabel">Prompt</span>
            <span className="composerMode">{selectedAction.replaceAll("_", " ")}</span>
          </div>
          <textarea
            ref={textareaRef}
            onKeyDown={handleKeyDown}
            onChange={(event) => onComposerTextChange(event.target.value)}
            placeholder={`Message AlphaMesh using ${selectedAction.replaceAll("_", " ")}...`}
            value={composerText}
          />
          <div className="composerMeta">
            <span>{replyPending ? "Running..." : "Natural language prompt"}</span>
            <button className="primaryButton" disabled={!canSend} onClick={onSend} type="button">
              Send
            </button>
          </div>
        </div>
        {replyError ? <p className="errorText">{replyError}</p> : null}
      </footer>
    </main>
  );
}

function ThreadNotice({ text, error = false }: { text: string; error?: boolean }) {
  return <div className={`threadNotice ${error ? "error" : ""}`}>{text}</div>;
}
