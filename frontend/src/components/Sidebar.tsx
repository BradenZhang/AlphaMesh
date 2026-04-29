import type { ConversationSummary } from "../types";
import { formatDateTime } from "../utils/format";

const DEFAULT_SYMBOL = "AAPL";

interface SidebarProps {
  conversationList: ConversationSummary[];
  activeConversationId: string | null;
  conversationListError: string | null;
  onSelectConversation: (id: string) => void;
  onCreateConversation: () => void;
}

export function Sidebar({
  conversationList,
  activeConversationId,
  conversationListError,
  onSelectConversation,
  onCreateConversation
}: SidebarProps) {
  return (
    <aside className="sidebarPanel">
      <div className="brandRow">
        <div className="brandBadge">AM</div>
        <div>
          <p className="eyebrow">AlphaMesh</p>
          <h1>Operator Chat</h1>
        </div>
      </div>

      <button className="primaryButton blockButton" onClick={onCreateConversation} type="button">
        New conversation
      </button>

      <section className="sidebarSection">
        <div className="sectionHeading">
          <span>Conversations</span>
          <small>{conversationList.length}</small>
        </div>
        <div className="conversationList">
          {conversationList.map((conversation) => (
            <button
              className={`conversationItem ${
                activeConversationId === conversation.conversation_id ? "active" : ""
              }`}
              key={conversation.conversation_id}
              onClick={() => onSelectConversation(conversation.conversation_id)}
              type="button"
            >
              <div className="conversationTopline">
                <strong>{conversation.title}</strong>
                <span className="symbolBadge">{conversation.symbol ?? DEFAULT_SYMBOL}</span>
              </div>
              <small>
                {conversation.message_count} messages
                <span className="dotDivider" />
                {formatDateTime(conversation.updated_at)}
              </small>
            </button>
          ))}
        </div>
        {conversationListError ? <p className="errorText">{conversationListError}</p> : null}
      </section>
    </aside>
  );
}
