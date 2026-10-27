import { useEffect, useMemo, useState } from "react";

import { getBenchmarks, startBenchmark } from "../api/client";
import { ArchitecturePicker, RunEstimate } from "../components/RunOptions";
import { DIFFICULTIES } from "../lib/format";
import { navigate } from "../lib/router";
import type { BenchmarkCase, LabConfig } from "../types/experiment";

export default function BenchmarkPage({ config }: { config: LabConfig | null }) {
  const [cases, setCases] = useState<BenchmarkCase[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [tier, setTier] = useState<string>("all");
  const [trials, setTrials] = useState(3);
  const [architectures, setArchitectures] = useState<string[]>(["1-agent", "2-agent", "3-agent", "4-agent"]);
  const [label, setLabel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    getBenchmarks()
      .then((data) => {
        setCases(data.cases);
        setSelected(new Set(data.cases.map((item) => item.case_id)));
      })
      .catch((exc: Error) => setError(exc.message));
  }, []);

  const visible = useMemo(
    () => cases.filter((item) => tier === "all" || item.difficulty === tier),
    [cases, tier],
  );

  const toggle = (caseId: string) => {
    const next = new Set(selected);
    if (next.has(caseId)) next.delete(caseId);
    else next.add(caseId);
    setSelected(next);
  };

  const selectTier = (name: string) => {
    setTier(name);
    setSelected(
      new Set(
        cases
          .filter((item) => name === "all" || item.difficulty === name)
          .map((item) => item.case_id),
      ),
    );
  };

  const start = async () => {
    setStarting(true);
    setError(null);

    try {
      const response = await startBenchmark({
        case_ids: [...selected],
        trials,
        architectures,
        label,
      });
      navigate(`/runs/${response.run_id}`);
    } catch (exc) {
      setError((exc as Error).message);
      setStarting(false);
    }
  };

  const isFull = selected.size === cases.length && trials === 3 && architectures.length === 4;

  return (
    <main className="app">
      <section className="experiment-header">
        <div className="eyebrow">FIXED BENCHMARK</div>
        <h1>Run the benchmark</h1>
        <p>
          Twelve research questions, from easy lookups to adversarial traps, each
          with frozen, curated evidence. Run all of them with 3 trials for the
          official result, or pick a subset to explore.
        </p>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <span className="panel-label">CASES · {selected.size} SELECTED</span>
            <h2>Choose cases</h2>
          </div>

          <div className="chip-row">
            {["all", ...DIFFICULTIES].map((name) => (
              <button
                key={name}
                type="button"
                className={tier === name ? "chip capitalize active" : "chip capitalize"}
                onClick={() => selectTier(name)}
              >
                {name}
              </button>
            ))}
          </div>
        </div>

        <div className="case-list">
          {visible.map((item) => (
            <label className="case-row" key={item.case_id}>
              <input
                type="checkbox"
                checked={selected.has(item.case_id)}
                onChange={() => toggle(item.case_id)}
              />
              <span className={`difficulty-tag ${item.difficulty}`}>{item.difficulty}</span>
              <span className="case-text">
                <strong>{item.question}</strong>
                <small>{item.design_notes}</small>
              </span>
              <span className="muted small-text">
                {item.sources} sources · {item.key_points} key points
              </span>
            </label>
          ))}
        </div>
      </section>

      {config && (
        <section className="panel">
          <div className="form-grid">
            <label>
              Trials per case
              <select value={trials} onChange={(event) => setTrials(Number(event.target.value))}>
                <option value={1}>1 (quick look)</option>
                <option value={2}>2</option>
                <option value={3}>3 (official)</option>
              </select>
            </label>

            <label>
              Label (optional)
              <input
                value={label}
                onChange={(event) => setLabel(event.target.value)}
                placeholder="e.g. official run #1"
              />
            </label>
          </div>

          <div className="field">
            <span className="field-label">Architectures</span>
            <ArchitecturePicker config={config} value={architectures} onChange={setArchitectures} />
          </div>

          <RunEstimate config={config} architectures={architectures} units={selected.size * trials} />

          {isFull && (
            <p className="muted small-text">
              This is the full, official configuration: 12 cases × 3 trials × 4 architectures.
            </p>
          )}

          {error && <div className="error-box">{error}</div>}

          <button
            className="primary-button full-width"
            disabled={starting || selected.size === 0 || architectures.length === 0 || !config.api_key_configured}
            onClick={start}
          >
            {starting ? "Starting…" : "Start benchmark"}
          </button>
        </section>
      )}
    </main>
  );
}
