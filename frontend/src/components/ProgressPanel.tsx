import { colorFor, statusLabel } from "../lib/format";
import type { JobStatus } from "../types/experiment";

interface ProgressPanelProps {
  status: JobStatus | null;
  architectures: string[];
  onResume?: () => void;
}

export default function ProgressPanel({
  status,
  architectures,
  onResume,
}: ProgressPanelProps) {
  if (!status) {
    return (
      <section className="panel progress-panel">
        <span className="panel-label">EXPERIMENT PROGRESS</span>
        <h2>Connecting…</h2>
      </section>
    );
  }

  const running = status.status === "running" || status.status === "queued";

  return (
    <section className="panel progress-panel">
      <div className="progress-header">
        <div>
          <span className="panel-label">
            EXPERIMENT PROGRESS · {statusLabel(status.status).toUpperCase()}
          </span>
          <h2>{status.message}</h2>
        </div>

        <strong>{status.progress}%</strong>
      </div>

      <div className="progress-track">
        <div
          className={running ? "progress-fill animated" : "progress-fill"}
          style={{ width: `${status.progress}%` }}
        />
      </div>

      <div className="progress-meta">
        <span>
          {status.current_case
            ? `Case ${status.current_case}${status.current_trial ? ` · trial ${status.current_trial}` : ""}`
            : "Preparing experiment"}
        </span>
        <span>Calls are rate-limited to stay inside the free tier.</span>
      </div>

      <div className="architecture-progress">
        {architectures.map((architecture) => (
          <div
            key={architecture}
            className={
              running && status.current_architecture === architecture
                ? "architecture-progress-item active"
                : "architecture-progress-item"
            }
          >
            <span className="architecture-dot" style={{ background: colorFor(architecture) }} />
            {architecture}
          </div>
        ))}
      </div>

      {status.events.length > 0 && (
        <ol className="event-feed">
          {[...status.events].reverse().map((event, index) => (
            <li key={`${event.time}-${index}`}>
              <time>{event.time}</time>
              {event.message}
            </li>
          ))}
        </ol>
      )}

      {status.status === "paused" && (
        <div className="notice-box">
          The run paused, usually because today's free-tier quota ran out.
          Everything finished so far is saved. Resume after the quota resets
          (midnight Pacific time): completed calls come from the cache and
          cost nothing.
          {onResume && (
            <button className="secondary-button small" onClick={onResume}>
              Resume now
            </button>
          )}
        </div>
      )}

      {status.error && status.status !== "paused" && (
        <div className="error-box">{status.error}</div>
      )}
    </section>
  );
}
