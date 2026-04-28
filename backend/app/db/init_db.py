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


@lru_cache
def init_db() -> None:
    last_error: OperationalError | None = None
    for _ in range(5):
        try:
            Base.metadata.create_all(bind=engine)
            _ensure_memory_columns()
            return
        except OperationalError as exc:
            last_error = exc
            sleep(1)
    if last_error is not None:
        raise last_error
