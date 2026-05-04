from functools import lru_cache
from time import sleep

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import engine


def _ensure_memory_columns() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("agent_memories"):
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("agent_memories")
    }
    statements: list[str] = []
    if "content_hash" not in existing_columns:
        statements.append("ALTER TABLE agent_memories ADD COLUMN content_hash VARCHAR(64)")
    if "token_keywords" not in existing_columns:
        statements.append("ALTER TABLE agent_memories ADD COLUMN token_keywords JSON")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_agent_memories_content_hash "
                "ON agent_memories (content_hash)"
            )
        )


def _ensure_additive_columns() -> None:
    inspector = inspect(engine)
    table_columns: dict[str, set[str]] = {}
    for table_name in ("chat_conversations", "agent_runs", "paper_orders"):
        if inspector.has_table(table_name):
            table_columns[table_name] = {
                column["name"] for column in inspector.get_columns(table_name)
            }

    statements: list[str] = []
    if "chat_conversations" in table_columns:
        existing = table_columns["chat_conversations"]
        if "market_provider" not in existing:
            statements.append(
                "ALTER TABLE chat_conversations ADD COLUMN market_provider VARCHAR(32)"
            )
        if "execution_provider" not in existing:
            statements.append(
                "ALTER TABLE chat_conversations ADD COLUMN execution_provider VARCHAR(32)"
            )
        if "account_provider" not in existing:
            statements.append(
                "ALTER TABLE chat_conversations ADD COLUMN account_provider VARCHAR(32)"
            )

    if "agent_runs" in table_columns:
        existing = table_columns["agent_runs"]
        if "market_provider" not in existing:
            statements.append("ALTER TABLE agent_runs ADD COLUMN market_provider VARCHAR(32)")
        if "execution_provider" not in existing:
            statements.append("ALTER TABLE agent_runs ADD COLUMN execution_provider VARCHAR(32)")
        if "account_provider" not in existing:
            statements.append("ALTER TABLE agent_runs ADD COLUMN account_provider VARCHAR(32)")

    if "paper_orders" in table_columns:
        existing = table_columns["paper_orders"]
        if "broker" not in existing:
            statements.append("ALTER TABLE paper_orders ADD COLUMN broker VARCHAR(32)")
        if "account_id" not in existing:
            statements.append("ALTER TABLE paper_orders ADD COLUMN account_id VARCHAR(64)")
        if "external_order_id" not in existing:
            statements.append(
                "ALTER TABLE paper_orders ADD COLUMN external_order_id VARCHAR(128)"
            )
        if "environment" not in existing:
            statements.append("ALTER TABLE paper_orders ADD COLUMN environment VARCHAR(32)")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


@lru_cache
def init_db() -> None:
    last_error: OperationalError | None = None
    for _ in range(5):
        try:
            Base.metadata.create_all(bind=engine)
            _ensure_memory_columns()
            _ensure_additive_columns()
            return
        except OperationalError as exc:
            last_error = exc
            sleep(1)
    if last_error is not None:
        raise last_error
