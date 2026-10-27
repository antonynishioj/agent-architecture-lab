import { useEffect, useState } from "react";

import { csvUrl, getRun, getSummary } from "../api/client";
import {
  DIFFICULTIES,
  DIMENSION_LABELS,
  colorFor,
  compact,
  percent,
  score,
  seconds,
  usd,
} from "../lib/format";
import type { RunDetail, Summary } from "../types/experiment";
import CaseExplorer from "./CaseExplorer";
import { BarChart, IntervalChart, TierChart, TradeoffChart } from "./charts";

export default function ResultsView({
  runId,
  refreshKey,
}: {
  runId: string;
  refreshKey: string;
}) {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    Promise.all([getSummary(runId), getRun(runId)])
      .then(([nextSummary, nextDetail]) => {
        if (cancelled) return;
        setSummary(nextSummary);
        setDetail(nextDetail);
      })
      .catch((exc: Error) => !cancelled && setError(exc.message));

    return () => {
      cancelled = true;
    };
  }, [runId, refreshKey]);

  if (error) return <div className="error-box">{error}</div>;
  if (!summary || !detail) return <p className="muted">Loading results…</p>;

  if (summary.config.units_completed === 0) {
    return <p className="muted">No completed case-trials yet. Results appear here as soon as the first one finishes.</p>;
  }

  const rows = summary.architectures;
  const winner = summary.winner;
  const tiers = DIFFICULTIES.filter((tier) => summary.by_difficulty[tier]);
  const partial = summary.config.units_completed < summary.config.units_planned;
  const singleCase = summary.config.cases_planned < 2;

  return (
    <section className="results">
      <div className="winner-banner">
        <div>
          <span className="panel-label">
            {partial ? "PROVISIONAL WINNER (RUN NOT FINISHED)" : "WINNER"}
          </span>
          <h2>
            {winner.winner ? (
              <>
                <i className="swatch" style={{ background: colorFor(winner.winner) }} />
                {winner.winner}
              </>
            ) : (
              "No winner yet"
            )}
          </h2>
          <p>{winner.explanation}</p>
          {singleCase && (
            <p className="muted small-text">
              Based on a single case: confidence intervals need several cases to mean anything.
            </p>
          )}
        </div>
        <div className="winner-rule">
          <span className="panel-label">THE RULE (DECIDED BEFORE RUNNING)</span>
          <p>{winner.rule}</p>
        </div>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Architecture</th>
              <th>Quality index (95% CI)</th>
              {Object.values(DIMENSION_LABELS).map((label) => (
                <th key={label}>{label}</th>
              ))}
              <th>Blind win rate</th>
              <th>Trap violations</th>
              <th>Tokens / answer</th>
              <th>Latency</th>
              <th>Cost if paid</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.architecture} className={row.architecture === winner.winner ? "highlight" : ""}>
                <td>
                  <i className="swatch" style={{ background: colorFor(row.architecture) }} />
                  {row.architecture}
                </td>
                <td>
                  <strong>{score(row.quality_index, 3)}</strong>{" "}
                  <span className="muted">
                    ({score(row.quality_ci_low)}–{score(row.quality_ci_high)})
                  </span>
                </td>
                {Object.keys(DIMENSION_LABELS).map((dimension) => (
                  <td key={dimension}>{score(row.dimensions[dimension])}</td>
                ))}
                <td>{percent(row.win_rate)}</td>
                <td>{percent(row.trap_violation_rate)}</td>
                <td>{compact(row.total_tokens)}</td>
                <td>{seconds(row.latency_s)}</td>
                <td>{usd(row.estimated_cost_usd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="chart-grid">
        <IntervalChart
          title="Quality index"
          subtitle="Mean over cases, with 95% bootstrap confidence interval"
          data={rows.map((row) => ({
            name: row.architecture,
            value: row.quality_index,
            low: row.quality_ci_low,
            high: row.quality_ci_high,
            detail: `${row.cases_scored} cases scored`,
          }))}
        />

        <TradeoffChart
          title="Quality vs cost"
          subtitle="Up and to the left is better"
          data={rows.map((row) => ({
            name: row.architecture,
            tokens: row.total_tokens,
            quality: row.quality_index,
          }))}
        />

        {tiers.length > 0 && (
          <TierChart
            title="Quality by difficulty"
            subtitle="Where (if anywhere) do extra agents pay off?"
            tiers={tiers}
            series={rows.map((row) => ({
              name: row.architecture,
              values: tiers.map((tier) => summary.by_difficulty[tier].quality_index[row.architecture] ?? null),
            }))}
          />
        )}

        <BarChart
          title="Tokens per answer"
          subtitle="Input + output + thinking, all agents"
          data={rows.map((row) => ({ name: row.architecture, value: row.total_tokens }))}
          format={(value) => Math.round(value).toLocaleString()}
        />

        <BarChart
          title="Latency per answer"
          subtitle="Sum of sequential call times"
          data={rows.map((row) => ({ name: row.architecture, value: row.latency_s }))}
          format={(value) => `${value.toFixed(1)} s`}
        />

        <BarChart
          title="Blind ranking: mean position"
          subtitle="1 = ranked best by the side-by-side judge (lower is better)"
          data={rows.map((row) => ({ name: row.architecture, value: row.mean_rank }))}
          format={(value) => value.toFixed(2)}
        />
      </div>

      <div className="two-column">
        {winner.comparisons.length > 0 && (
          <div className="panel">
            <span className="panel-label">IS EACH ARCHITECTURE AS GOOD AS {winner.best_quality?.toUpperCase()}?</span>
            <table className="data-table compact-table">
              <thead>
                <tr>
                  <th>Architecture</th>
                  <th>Gap</th>
                  <th>95% CI</th>
                  <th>As good?</th>
                </tr>
              </thead>
              <tbody>
                {winner.comparisons.map((comparison) => (
                  <tr key={comparison.architecture}>
                    <td>{comparison.architecture}</td>
                    <td>{score(comparison.diff_mean, 3)}</td>
                    <td>
                      {score(comparison.ci_low, 3)} to {score(comparison.ci_high, 3)}
                    </td>
                    <td>{comparison.as_good_as_best ? "yes" : "no"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="panel">
          <span className="panel-label">ROBUSTNESS TO SCORING WEIGHTS</span>
          <table className="data-table compact-table">
            <thead>
              <tr>
                <th>Scheme</th>
                <th>Best quality</th>
                <th>Winner</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(summary.sensitivity).map(([scheme, result]) => (
                <tr key={scheme}>
                  <td>{scheme.replace(/_/g, " ")}</td>
                  <td>{result.best_quality ?? "–"}</td>
                  <td>{result.winner ?? "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {tiers.length > 0 && (
        <div className="panel">
          <span className="panel-label">WINNER PER DIFFICULTY TIER</span>
          <table className="data-table compact-table">
            <thead>
              <tr>
                <th>Tier</th>
                {summary.config.architectures.map((name) => (
                  <th key={name}>{name}</th>
                ))}
                <th>Best quality</th>
                <th>Winner</th>
              </tr>
            </thead>
            <tbody>
              {tiers.map((tier) => {
                const row = summary.by_difficulty[tier];
                return (
                  <tr key={tier}>
                    <td>
                      {tier} <span className="muted">({row.cases})</span>
                    </td>
                    {summary.config.architectures.map((name) => (
                      <td key={name}>{score(row.quality_index[name], 3)}</td>
                    ))}
                    <td>{row.best_quality}</td>
                    <td>
                      <strong>{row.winner}</strong>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="results-actions">
        <a className="secondary-button" href={csvUrl(runId)}>
          Download CSV
        </a>
        <span className="muted">
          Saved in <code>results/runs/{detail.manifest.directory}</code>. Commit that folder so others can verify it.
        </span>
      </div>

      <CaseExplorer detail={detail} />
    </section>
  );
}
