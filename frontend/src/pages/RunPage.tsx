import { useEffect, useState } from "react";

import { getRun, resumeRun } from "../api/client";
import ProgressPanel from "../components/ProgressPanel";
import ResultsView from "../components/ResultsView";
import { statusLabel } from "../lib/format";
import { isTerminal, useRunProgress } from "../lib/useRunProgress";
import type { RunManifest } from "../types/experiment";

export default function RunPage({ runId }: { runId: string }) {
  const [manifest, setManifest] = useState<RunManifest | null>(null);
  const [resumeKey, setResumeKey] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const status = useRunProgress(runId, resumeKey);

  useEffect(() => {
    getRun(runId)
      .then((detail) => setManifest(detail.manifest))
      .catch((exc: Error) => setError(exc.message));
  }, [runId, status?.status]);

  const resume = async () => {
    setError(null);

    try {
      await resumeRun(runId);
      setResumeKey((key) => key + 1);
    } catch (exc) {
      setError((exc as Error).message);
    }
  };

  const live = status !== null && !isTerminal(status.status);
  const canResume = manifest && ["paused", "failed", "completed_with_errors"].includes(manifest.status) && !live;

  // Refresh results whenever a new case-trial starts (so the previous one
  // has just been saved) and once more when the run ends.
  const refreshKey = `${status?.status}-${status?.current_case}-${status?.current_trial}`;

  return (
    <main className="app">
      <section className="experiment-header">
        <div className="eyebrow">
          {manifest ? `${manifest.run_type.toUpperCase()} RUN · ${statusLabel(manifest.status).toUpperCase()}` : "RUN"}
        </div>
        <h1>{manifest?.label || `Run ${runId}`}</h1>
        {manifest && (
          <p>
            {manifest.case_ids.length} case{manifest.case_ids.length === 1 ? "" : "s"} × {manifest.trials} trial
            {manifest.trials === 1 ? "" : "s"} · generator <code>{manifest.generator_model}</code> · judge{" "}
            <code>{manifest.judge_model}</code> · saved in <code>results/runs/{manifest.directory}</code>
          </p>
        )}
      </section>

      {error && <div className="error-box">{error}</div>}

      {manifest && (live || status?.status === "paused") && (
        <ProgressPanel status={status} architectures={manifest.architectures} onResume={resume} />
      )}

      {canResume && status?.status !== "paused" && (
        <div className="notice-box">
          {manifest.status === "completed_with_errors"
            ? "Some case-trials failed. Resuming retries only those; finished ones are kept."
            : "This run did not finish. Resuming continues where it stopped; cached calls cost nothing."}
          <button className="secondary-button small" onClick={resume}>
            Resume run
          </button>
        </div>
      )}

      <ResultsView runId={runId} refreshKey={refreshKey} />
    </main>
  );
}
