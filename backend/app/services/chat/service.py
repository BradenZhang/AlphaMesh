import re
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func

from app.db.init_db import init_db
from app.db.models import ChatConversationRecord, ChatMessageRecord
from app.db.session import SessionLocal
from app.domain.enums import AutomationMode, StrategyName
from app.schemas.automation import AutomationRunRequest
from app.schemas.chat import (
    ChatArtifactSchema,
    ChatMessageSchema,
    ChatReplyRequest,
    ChatReplyResponse,
    ConversationCreateRequest,
    ConversationDetail,
    ConversationSummary,
    ConversationUpdateRequest,
)
from app.services.agents.react_runtime import ReActRuntime
from app.services.agents.research_workflow import MultiAgentResearchWorkflow
from app.services.agents.runtime import AgentRuntime
from app.services.agents.tool_registry import ToolRegistry
from app.services.automation.flow import AutomationFlow
from app.services.case.store import InvestmentCaseStore
from app.services.llm.factory import get_llm_provider_for_profile


class ChatConversationNotFoundError(ValueError):
    pass


class ChatService:
    def __init__(self) -> None:
        init_db()
        self.case_store = InvestmentCaseStore()

    def list_conversations(self, user_id: str = "default") -> list[ConversationSummary]:
        with SessionLocal() as session:
            conversations = (
                session.query(ChatConversationRecord)
                .filter(ChatConversationRecord.user_id == user_id)
                .order_by(ChatConversationRecord.updated_at.desc())
                .all()
            )
            counts = {
                conversation_id: message_count
                for conversation_id, message_count in (
                    session.query(
                        ChatMessageRecord.conversation_id,
                        func.count(ChatMessageRecord.id),
                    )
                    .group_by(ChatMessageRecord.conversation_id)
                    .all()
                )
            }
            return [
                self._to_conversation_summary(record, counts.get(record.conversation_id, 0))
                for record in conversations
            ]

    def create_conversation(
        self,
        request: ConversationCreateRequest,
    ) -> ConversationSummary:
        now = self._now()
        record = ChatConversationRecord(
            conversation_id=f"conv-{uuid4().hex}",
            title="New Chat",
            symbol=request.symbol.upper() if request.symbol else "AAPL",
            llm_profile_id=request.llm_profile_id,
            strategy_name=(request.strategy_name or StrategyName.MOVING_AVERAGE_CROSS).value,
            market_provider=request.market_provider,
            execution_provider=request.execution_provider,
            account_provider=request.account_provider,
            user_id=request.user_id,
            created_at=now,
            updated_at=now,
        )
        with SessionLocal() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_conversation_summary(record, 0)

    def get_conversation(
        self,
        conversation_id: str,
        user_id: str = "default",
    ) -> ConversationDetail:
        with SessionLocal() as session:
            record = self._get_conversation_record(session, conversation_id, user_id)
            messages = (
                session.query(ChatMessageRecord)
                .filter(ChatMessageRecord.conversation_id == conversation_id)
                .order_by(ChatMessageRecord.created_at.asc(), ChatMessageRecord.id.asc())
                .all()
            )
            return ConversationDetail(
                **self._to_conversation_summary(record, len(messages)).model_dump(),
                messages=[self._to_message_schema(message) for message in messages],
            )

    def update_conversation(
        self,
        conversation_id: str,
        request: ConversationUpdateRequest,
        user_id: str = "default",
    ) -> ConversationSummary:
        with SessionLocal() as session:
            record = self._get_conversation_record(session, conversation_id, user_id)
            if request.symbol is not None:
                record.symbol = request.symbol.upper() if request.symbol else None
            if request.llm_profile_id is not None:
                record.llm_profile_id = request.llm_profile_id
            if request.strategy_name is not None:
                record.strategy_name = request.strategy_name.value
            if request.market_provider is not None:
                record.market_provider = request.market_provider
            if request.execution_provider is not None:
                record.execution_provider = request.execution_provider
            if request.account_provider is not None:
                record.account_provider = request.account_provider
            if request.title is not None:
                record.title = request.title.strip()
            record.updated_at = self._now()
            session.commit()
            message_count = self._count_messages(session, record.conversation_id)
            return self._to_conversation_summary(record, message_count)

    def reply(
        self,
        conversation_id: str,
        request: ChatReplyRequest,
        user_id: str = "default",
    ) -> ChatReplyResponse:
        context = self._prepare_context(conversation_id, request, user_id)
        assistant_content = ""
        assistant_artifacts: list[ChatArtifactSchema] = []
        assistant_status = "completed"

        try:
            assistant_content, assistant_artifacts = self._run_action(context, request)
        except Exception as exc:
            assistant_content = f"Request failed: {exc}"
            assistant_status = "error"
            assistant_message = self._append_assistant_message(
                conversation_id,
                assistant_content,
                request.action,
                assistant_artifacts,
                assistant_status,
            )
            raise
        else:
            assistant_message = self._append_assistant_message(
                conversation_id,
                assistant_content,
                request.action,
                assistant_artifacts,
                assistant_status,
            )

        conversation = self.get_conversation_summary(conversation_id, user_id)
        return ChatReplyResponse(
            conversation=conversation,
            user_message=context["user_message"],
            assistant_message=assistant_message,
        )

    def get_conversation_summary(
        self,
        conversation_id: str,
        user_id: str = "default",
    ) -> ConversationSummary:
        with SessionLocal() as session:
            record = self._get_conversation_record(session, conversation_id, user_id)
            return self._to_conversation_summary(
                record,
                self._count_messages(session, conversation_id),
            )

    def _prepare_context(
        self,
        conversation_id: str,
        request: ChatReplyRequest,
        user_id: str,
    ) -> dict[str, object]:
        with SessionLocal() as session:
            conversation = self._get_conversation_record(session, conversation_id, user_id)
            symbol = (request.symbol or conversation.symbol or "AAPL").upper()
            llm_profile_id = (
                request.llm_profile_id
                if request.llm_profile_id is not None
                else conversation.llm_profile_id
            )
            strategy_name = (
                request.strategy_name.value
                if request.strategy_name is not None
                else conversation.strategy_name or StrategyName.MOVING_AVERAGE_CROSS.value
            )
            market_provider = (
                request.market_provider
                if request.market_provider is not None
                else conversation.market_provider
            )
            execution_provider = (
                request.execution_provider
                if request.execution_provider is not None
                else conversation.execution_provider
            )
            account_provider = (
                request.account_provider
                if request.account_provider is not None
                else conversation.account_provider
            )

            conversation.symbol = symbol
            conversation.llm_profile_id = llm_profile_id
            conversation.strategy_name = strategy_name
            conversation.market_provider = market_provider
            conversation.execution_provider = execution_provider
            conversation.account_provider = account_provider
            if conversation.title.strip().lower() == "new chat":
                conversation.title = self._build_title(request.message)
            conversation.updated_at = self._now()

            user_record = ChatMessageRecord(
                message_id=f"msg-{uuid4().hex}",
                conversation_id=conversation_id,
                role="user",
                action=request.action,
                content=request.message.strip(),
                artifacts_payload=[],
                status="completed",
                created_at=self._now(),
            )
            session.add(user_record)
            session.commit()
            session.refresh(conversation)
            session.refresh(user_record)

            return {
                "symbol": symbol,
                "llm_profile_id": llm_profile_id,
                "strategy_name": strategy_name,
                "market_provider": market_provider,
                "execution_provider": execution_provider,
                "account_provider": account_provider,
                "conversation_id": conversation_id,
                "user_message": self._to_message_schema(user_record),
            }

    def _append_assistant_message(
        self,
        conversation_id: str,
        content: str,
        action: str,
        artifacts: list[ChatArtifactSchema],
        status: str,
    ) -> ChatMessageSchema:
        with SessionLocal() as session:
            conversation = self._get_conversation_record(session, conversation_id, "default")
            conversation.updated_at = self._now()
            message = ChatMessageRecord(
                message_id=f"msg-{uuid4().hex}",
                conversation_id=conversation_id,
                role="assistant",
                action=action,
                content=content,
                artifacts_payload=[artifact.model_dump(mode="json") for artifact in artifacts],
                status=status,
                created_at=self._now(),
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            return self._to_message_schema(message)

    def _run_action(
        self,
        context: dict[str, object],
        request: ChatReplyRequest,
    ) -> tuple[str, list[ChatArtifactSchema]]:
        symbol = str(context["symbol"])
        llm_profile_id = context["llm_profile_id"]
        strategy_name = str(context["strategy_name"])
        market_provider = context.get("market_provider")
        execution_provider = context.get("execution_provider")
        account_provider = context.get("account_provider")

        if request.action == "chat":
            provider = get_llm_provider_for_profile(
                llm_profile_id if isinstance(llm_profile_id, str) else None
            )
            result = ReActRuntime(
                llm_provider=provider,
                tool_registry=ToolRegistry(
                    market_provider_name=(
                        str(market_provider) if market_provider else None
                    )
                ),
            ).run(
                symbol=symbol,
                question=request.message.strip(),
                llm_profile_id=llm_profile_id if isinstance(llm_profile_id, str) else None,
            )
            return result.final_answer, [
                ChatArtifactSchema(
                    type="react_trace",
                    title="ReAct Trace",
                    payload=result.model_dump(mode="json"),
                )
            ]

        if request.action == "research":
            provider = get_llm_provider_for_profile(
                llm_profile_id if isinstance(llm_profile_id, str) else None
            )
            result = MultiAgentResearchWorkflow(
                runtime=AgentRuntime(
                    llm_provider=provider,
                    tool_registry=ToolRegistry(
                        market_provider_name=str(market_provider) if market_provider else None
                    ),
                )
            ).run(symbol)
            case = self.case_store.create(
                symbol=symbol,
                thesis=result.research_report.summary,
                confidence=result.committee_report.confidence_score,
                risks=result.research_report.risks,
                data_sources=result.research_report.data_sources,
                decision=result.committee_report.action_bias.lower(),
                conversation_id=str(context.get("conversation_id")),
            )
            return self._summarize_research(result), [
                ChatArtifactSchema(
                    type="multi_agent_report",
                    title="Multi-Agent Research",
                    payload={**result.model_dump(mode="json"), "case_id": case.case_id},
                ),
                ChatArtifactSchema(
                    type="research_report",
                    title="Research Report",
                    payload=result.research_report.model_dump(mode="json"),
                ),
            ]

        automation_mode = (
            AutomationMode.MANUAL
            if request.action == "manual_plan"
            else AutomationMode.PAPER_AUTO
        )
        result = AutomationFlow().run(
            AutomationRunRequest(
                symbol=symbol,
                mode=automation_mode,
                strategy_name=StrategyName(strategy_name),
                llm_profile_id=llm_profile_id if isinstance(llm_profile_id, str) else None,
                market_provider=str(market_provider) if market_provider else None,
                execution_provider=str(execution_provider) if execution_provider else None,
                account_provider=str(account_provider) if account_provider else None,
            )
        )
        artifacts = [
            ChatArtifactSchema(
                type="automation_result",
                title="Automation Result",
                payload=result.model_dump(mode="json"),
            )
        ]
        if result.order is not None:
            artifacts.append(
                ChatArtifactSchema(
                    type="paper_order",
                    title="Paper Order",
                    payload=result.order.model_dump(mode="json"),
                )
            )
        return self._summarize_automation(result), artifacts

    def _get_conversation_record(self, session, conversation_id: str, user_id: str):
        record = (
            session.query(ChatConversationRecord)
            .filter(
                ChatConversationRecord.conversation_id == conversation_id,
                ChatConversationRecord.user_id == user_id,
            )
            .first()
        )
        if record is None:
            raise ChatConversationNotFoundError(
                f"Conversation '{conversation_id}' was not found."
            )
        return record

    def _count_messages(self, session, conversation_id: str) -> int:
        return (
            session.query(func.count(ChatMessageRecord.id))
            .filter(ChatMessageRecord.conversation_id == conversation_id)
            .scalar()
            or 0
        )

    def _to_conversation_summary(
        self,
        record: ChatConversationRecord,
        message_count: int,
    ) -> ConversationSummary:
        return ConversationSummary(
            conversation_id=record.conversation_id,
            title=record.title,
            symbol=record.symbol,
            llm_profile_id=record.llm_profile_id,
            strategy_name=(
                StrategyName(record.strategy_name) if record.strategy_name else None
            ),
            market_provider=record.market_provider,
            execution_provider=record.execution_provider,
            account_provider=record.account_provider,
            user_id=record.user_id,
            message_count=message_count,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _to_message_schema(self, record: ChatMessageRecord) -> ChatMessageSchema:
        return ChatMessageSchema(
            message_id=record.message_id,
            conversation_id=record.conversation_id,
            role=record.role,  # type: ignore[arg-type]
            action=record.action,  # type: ignore[arg-type]
            content=record.content,
            artifacts=[
                ChatArtifactSchema.model_validate(artifact)
                for artifact in (record.artifacts_payload or [])
            ],
            status=record.status,  # type: ignore[arg-type]
            created_at=record.created_at,
        )

    def _build_title(self, message: str) -> str:
        cleaned = re.sub(r"\s+", " ", message.strip())
        if not cleaned:
            return "New Chat"
        return cleaned[:60]

    def _summarize_research(self, result) -> str:
        bias = result.committee_report.action_bias
        confidence = result.committee_report.confidence_score
        return (
            f"Research completed for {result.symbol}. "
            f"Committee bias: {bias}. "
            f"Confidence: {confidence:.0%}. "
            f"{result.committee_report.summary}"
        )

    def _summarize_automation(self, result) -> str:
        return (
            f"{result.symbol} {result.mode} completed. "
            f"Action {result.strategy_signal.action} at "
            f"{result.strategy_signal.confidence:.0%} confidence. "
            f"Risk: {result.risk_result.risk_level}. "
            f"{result.message}"
        )

    def _now(self) -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)
