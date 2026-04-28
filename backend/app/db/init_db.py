from functools import lru_cache
from time import sleep

from sqlalchemy.exc import OperationalError

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.session import engine


@lru_cache
def init_db() -> None:
    last_error: OperationalError | None = None
    for _ in range(5):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as exc:
            last_error = exc
            sleep(1)
    if last_error is not None:
        raise last_error
