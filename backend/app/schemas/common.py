import time
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel


class RunStep(BaseModel):
    step_id: str
    label: str
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0
    summary: str | None = None
    error: str | None = None


class StepTracker:
    """Wraps each pipeline phase with timing and status tracking."""

    def __init__(self) -> None:
        self.steps: list[RunStep] = []

    def run_step(
        self,
        step_id: str,
        label: str,
        fn,
        *,
        skip: bool = False,
    ):
        if skip:
            self.steps.append(RunStep(step_id=step_id, label=label, status="skipped"))
            return None

        step = RunStep(
            step_id=step_id,
            label=label,
            status="running",
            started_at=datetime.now(UTC),
        )
        self.steps.append(step)
        tick = time.perf_counter()
        try:
            result = fn()
            step.status = "completed"
            step.duration_ms = int((time.perf_counter() - tick) * 1000)
            step.completed_at = datetime.now(UTC)
            return result
        except Exception as exc:
            step.status = "failed"
            step.duration_ms = int((time.perf_counter() - tick) * 1000)
            step.completed_at = datetime.now(UTC)
            step.error = str(exc)
            raise
