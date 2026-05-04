import type { RunStep } from "../types";

interface WorkflowTimelineProps {
  runSteps: RunStep[];
  onRetry?: () => void;
  retrying?: boolean;
}

export function WorkflowTimeline({ runSteps, onRetry, retrying }: WorkflowTimelineProps) {
  if (!runSteps.length) return null;

  const hasFailed = runSteps.some((step) => step.status === "failed");

  return (
    <div className="workflowTimeline">
      {runSteps.map((step) => (
        <div className="timelineStep" key={step.step_id}>
          <div className={`timelineDot ${step.status}`}>
            {step.status === "completed" ? "✓" : step.status === "failed" ? "!" : step.status === "running" ? "●" : "–"}
          </div>
          <div className="timelineInfo">
            <span className="timelineLabel">{step.label}</span>
            {step.summary ? <span className="timelineSummary">{step.summary}</span> : null}
            {step.error ? <span className="timelineError">{step.error}</span> : null}
          </div>
          {step.duration_ms > 0 ? (
            <span className="timelineDuration">{step.duration_ms}ms</span>
          ) : null}
        </div>
      ))}
      {hasFailed && onRetry ? (
        <button
          className="ghostButton retryButton"
          onClick={onRetry}
          disabled={retrying}
          type="button"
        >
          {retrying ? "Retrying..." : "Retry Failed Steps"}
        </button>
      ) : null}
    </div>
  );
}
