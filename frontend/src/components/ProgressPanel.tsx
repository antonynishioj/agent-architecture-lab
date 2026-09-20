import type {
  ExperimentStatusResponse,
} from "../types/experiment";

interface ProgressPanelProps {
  status: ExperimentStatusResponse | null;
}

const architectures = [
  "1-agent",
  "2-agent",
  "3-agent",
  "4-agent",
];

export default function ProgressPanel({
  status,
}: ProgressPanelProps) {
  if (!status) {
    return null;
  }

  return (
    <section className="progress-panel">
      <div className="progress-header">
        <div>
          <span className="panel-label">
            EXPERIMENT PROGRESS
          </span>

          <h2>
            {status.message}
          </h2>
        </div>

        <strong>
          {status.progress}%
        </strong>
      </div>

      <div className="progress-track">
        <div
          className="progress-fill"
          style={{
            width: `${status.progress}%`,
          }}
        />
      </div>

      <div className="progress-meta">
        <span>
          {status.current_case ||
            "Preparing experiment"}
        </span>

        {status.current_architecture && (
          <span>
            {status.current_architecture}
          </span>
        )}
      </div>

      <div className="architecture-progress">
        {architectures.map((architecture) => {
          const current =
            status.current_architecture ===
            architecture;

          return (
            <div
              key={architecture}
              className={
                current
                  ? "architecture-progress-item active"
                  : "architecture-progress-item"
              }
            >
              <span className="architecture-dot" />
              {architecture}
            </div>
          );
        })}
      </div>

      {status.error && (
        <div className="error-box">
          {status.error}
        </div>
      )}
    </section>
  );
}