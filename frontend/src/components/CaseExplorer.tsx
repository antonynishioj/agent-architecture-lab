import { useMemo, useState } from "react";

import { DIMENSION_LABELS, colorFor, compact, score, seconds } from "../lib/format";
import type { Outcome, RunDetail } from "../types/experiment";
import Markdown from "./Markdown";

const ROLE_TITLES: Record<string, string> = {
  research: "Research",
  fact_check: "Fact-check",
  critic: "Critique",
  writer: "Writing",
};

export default function CaseExplorer({ detail }: { detail: RunDetail }) {
  const items = detail.items;
  const [selected, setSelected] = useState(() =>
    items.length ? `${items[0].case_id}::${items[0].trial}` : "",
  );

  const item = useMemo(
    () => items.find((entry) => `${entry.case_id}::${entry.trial}` === selected) ?? items[0],
    [items, selected],
  );

  if (!item) return null;

  const definition = detail.cases.find((entry) => entry.case_id === item.case_id);
  const sources = definition?.research?.results ?? [];
  const rankOf = (name: string) => (item.ranking ? item.ranking.order.indexOf(name) + 1 : null);

  return (
    <section className="case-explorer">
      <div className="section-heading">
        <div>
          <div className="eyebrow">DRILL DOWN</div>
          <h2>Answers side by side</h2>
        </div>

        <select value={selected} onChange={(event) => setSelected(event.target.value)}>
          {items.map((entry) => (
            <option key={`${entry.case_id}::${entry.trial}`} value={`${entry.case_id}::${entry.trial}`}>
              [{entry.difficulty}] {entry.case_id} · trial {entry.trial}
            </option>
          ))}
        </select>
      </div>

      <div className="panel case-question">
        <span className="panel-label">
          {item.category.toUpperCase()} · {item.difficulty.toUpperCase()}
        </span>
        <h3>{item.question}</h3>

        {definition?.design_notes && <p className="muted">Why this case: {definition.design_notes}</p>}

        <div className="case-meta">
          {definition && definition.key_points.length > 0 && (
            <details>
              <summary>Key points ({definition.key_points.length})</summary>
              <ul>
                {definition.key_points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </details>
          )}

          {definition && definition.must_not_claim.length > 0 && (
            <details>
              <summary>Trap claims ({definition.must_not_claim.length})</summary>
              <ul>
                {definition.must_not_claim.map((claim) => (
                  <li key={claim}>{claim}</li>
                ))}
              </ul>
            </details>
          )}

          <details>
            <summary>Sources ({sources.length})</summary>
            <ol className="source-list">
              {sources.map((source, index) => (
                <li key={index}>
                  <strong>
                    [S{index + 1}] {source.title}
                  </strong>
                  {source.published && <span className="muted"> · {source.published}</span>}
                  <p>{source.content}</p>
                </li>
              ))}
            </ol>
          </details>
        </div>

        {item.ranking && (
          <details>
            <summary>Blind ranking judge: {item.ranking.order.join(" > ")}</summary>
            <p className="reasoning">{item.ranking.reasoning}</p>
            <p className="muted small-text">
              Labels shown to the judge:{" "}
              {Object.entries(item.ranking.labels)
                .map(([label, name]) => `${label} = ${name}`)
                .join(", ")}
            </p>
          </details>
        )}
      </div>

      <div className="answer-grid">
        {item.outcomes.map((outcome) => (
          <OutcomeCard key={outcome.architecture} outcome={outcome} rank={rankOf(outcome.architecture)} />
        ))}
      </div>
    </section>
  );
}

function OutcomeCard({ outcome, rank }: { outcome: Outcome; rank: number | null }) {
  const evaluation = outcome.evaluation;
  const quality = evaluation
    ? Object.keys(DIMENSION_LABELS).reduce(
        (total, key) => total + (evaluation[key as keyof typeof evaluation] as number),
        0,
      ) / 6
    : null;

  return (
    <article className="answer-card">
      <header>
        <h3>
          <i className="swatch" style={{ background: colorFor(outcome.architecture) }} />
          {outcome.architecture}
        </h3>
        <span className="agent-badge">
          {rank ? `ranked #${rank}` : outcome.status}
        </span>
      </header>

      {outcome.error && <div className="error-box">{outcome.error}</div>}

      {evaluation && (
        <div className="score-strip">
          <div>
            <span>Quality</span>
            <strong>{score(quality)}</strong>
          </div>
          {Object.entries(DIMENSION_LABELS).map(([key, label]) => (
            <div key={key}>
              <span>{label}</span>
              <strong>{score(evaluation[key as keyof typeof evaluation] as number)}</strong>
            </div>
          ))}
        </div>
      )}

      <div className="answer-stats">
        {outcome.call_count} calls · {compact(outcome.total_tokens)} tokens · {seconds(outcome.latency_ms / 1000)}
        {outcome.deterministic && (
          <>
            {" "}
            · {outcome.deterministic.citation_count} citations
            {outcome.deterministic.invalid_citations > 0 && (
              <span className="warn"> ({outcome.deterministic.invalid_citations} invalid)</span>
            )}
          </>
        )}
      </div>

      <div className="answer">
        <Markdown text={outcome.answer} />
      </div>

      {evaluation && evaluation.trap_violations.length > 0 && (
        <div className="error-box">
          Trap violations: {evaluation.trap_violations.join("; ")}
        </div>
      )}

      {evaluation && (
        <details>
          <summary>Judge reasoning</summary>
          <p className="reasoning">{evaluation.reasoning}</p>
          {evaluation.unsupported_claims.length > 0 && (
            <>
              <p className="muted">Unsupported claims:</p>
              <ul>
                {evaluation.unsupported_claims.map((claim) => (
                  <li key={claim}>{claim}</li>
                ))}
              </ul>
            </>
          )}
          {evaluation.key_points.length > 0 && (
            <ul className="key-point-list">
              {evaluation.key_points.map((point) => (
                <li key={point.point} className={point.status}>
                  <b>{point.status}</b> {point.point}
                </li>
              ))}
            </ul>
          )}
        </details>
      )}

      {outcome.judge_error && <div className="error-box">Judge error: {outcome.judge_error}</div>}

      {outcome.steps.length > 1 && (
        <details>
          <summary>Agent trace ({outcome.steps.length} agents)</summary>
          {outcome.steps.map((step) => (
            <div key={step.agent_index} className="trace-step">
              <div className="trace-head">
                Agent {step.agent_index + 1}: {step.roles.map((role) => ROLE_TITLES[role] ?? role).join(" + ")}
                <span className="muted">
                  {" "}
                  · {compact(step.input_tokens)} in / {compact(step.output_tokens)} out ·{" "}
                  {seconds(step.latency_ms / 1000)} · {step.saw_sources ? "saw sources" : "notes only"}
                </span>
              </div>
              <pre>{step.output}</pre>
            </div>
          ))}
        </details>
      )}
    </article>
  );
}
