import logging
import time
from abc import ABC, abstractmethod

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.services.llm.schemas import LLMMessage, LLMProviderInfo, LLMResponse

logger = logging.getLogger(__name__)

# Retryable error types (network / transient server errors)
_RETRYABLE_EXCEPTIONS = (ConnectionError, TimeoutError, OSError)


def _make_retry_decorator(max_retries: int = 3):
    """Build a tenacity retry decorator for LLM calls."""
    if max_retries <= 0:
        # No-op decorator
        def _noop(fn):
            return fn

        return _noop

    return retry(
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=lambda retry_state: logger.warning(
            "LLM call failed (attempt %d/%d), retrying in %.1fs: %s",
            retry_state.attempt_number,
            max_retries,
            retry_state.next_action.sleep if retry_state.next_action else 0,
            retry_state.outcome.exception() if retry_state.outcome else "unknown",
        ),
        reraise=True,
    )


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
    ) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    def get_provider_info(self) -> LLMProviderInfo:
        raise NotImplementedError

    def _timed_call(self, label: str, fn, *args, **kwargs):
        """Execute a callable with timing and logging."""
        started = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            logger.debug("%s completed in %dms", label, elapsed_ms)
            return result
        except Exception:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            logger.warning("%s failed after %dms", label, elapsed_ms)
            raise
