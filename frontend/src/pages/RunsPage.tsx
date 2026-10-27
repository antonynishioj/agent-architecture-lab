import { useEffect, useState } from "react";

import { listRuns } from "../api/client";
import { statusLabel } from "../lib/format";
import { navigate } from "../lib/router";
import type { RunListItem } from "../types/experiment";

export default function RunsPage() {
  const [runs, setRuns] = useState<RunListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listRuns().then(setRuns).catch((exc: Error) => setError(exc.message));
  }, []);

  return (
    <main className="app">
      <section className="experiment-header">
        <div className="eyebrow">RUN HISTORY</div>
        <h1>Past runs</h1>
        <p>
          Every run is saved under <code>results/runs/</code> with its full
          configuration, every prompt and response, and the computed summary.
          Commit the folder and anyone can verify it.
        </p>
      </section>

      {error && <div className="error-box">{error}</div>}
      {runs && runs.length === 0 && <p className="muted">No runs yet.</p>}

      <div className="run-list">
        {runs?.map((run) => (
          <button className="run-row" key={run.run_id} onClick={() => navigate(`/runs/${run.run_id}`)}>
            <span className={`status-badge ${run.status}`}>{statusLabel(run.status)}</span>
            <span className="run-text">
              <strong>{run.label || `${run.run_type} run`}</strong>
              <small>
                {run.case_count} case{run.case_count === 1 ? "" : "s"} × {run.trials} trial
                {run.trials === 1 ? "" : "s"} · {run.architectures.join(", ")} · {run.generator_model}
              </small>
            </span>
            <span className="muted small-text">
              {run.completed_items}/{run.total_items} done
              {run.failed_items > 0 && ` · ${run.failed_items} failed`}
            </span>
            <span className="muted small-text">{new Date(run.created_at).toLocaleString()}</span>
          </button>
        ))}
      </div>
    </main>
  );
}
