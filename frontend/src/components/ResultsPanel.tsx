import type {
  EvaluatedArchitectureResult,
} from "../types/experiment";

interface ResultsPanelProps {
  results: EvaluatedArchitectureResult[];
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}


function formatLatency(
  milliseconds: number,
): string {
  if (milliseconds < 1000) {
    return `${Math.round(milliseconds)} ms`;
  }

  return `${(
    milliseconds / 1000
  ).toFixed(2)} s`;
}


function formatCost(
  cost: number | null,
): string {
  if (cost === null) {
    return "Not configured";
  }

  return `$${cost.toFixed(6)}`;
}


export default function ResultsPanel({
  results,
}: ResultsPanelProps) {
  return (
    <section className="results-section">
      <div className="section-heading">
        <div>
          <div className="eyebrow">
            RESULTS
          </div>

          <h2>
            Architecture measurements
          </h2>
        </div>

        <p>
          Each architecture is evaluated independently.
          The measurements should be interpreted as
          trade-offs rather than a single ranking.
        </p>
      </div>

      <div className="results-grid">
        {results.map((item) => {
          const architecture =
            item.architecture;

          const evaluation =
            item.evaluation;

          return (
            <article
              className="result-card"
              key={
                architecture.architecture_name
              }
            >
              <div className="result-card-header">
                <div>
                  <span className="card-number">
                    {String(
                      architecture.agent_count,
                    ).padStart(2, "0")}
                  </span>

                  <h3>
                    {architecture.architecture_name}
                  </h3>
                </div>

                <span className="agent-badge">
                  {architecture.agent_count}{" "}
                  {architecture.agent_count === 1
                    ? "agent"
                    : "agents"}
                </span>
              </div>

              <div className="quality-grid">
                <Metric
                  label="Relevancy"
                  value={formatPercent(
                    evaluation.answer_relevancy,
                  )}
                />

                <Metric
                  label="Completeness"
                  value={formatPercent(
                    evaluation.completeness,
                  )}
                />

                <Metric
                  label="Faithfulness"
                  value={formatPercent(
                    evaluation.faithfulness,
                  )}
                />

                <Metric
                  label="Overall"
                  value={formatPercent(
                    evaluation.overall_quality,
                  )}
                />
              </div>

              <div className="execution-metrics">
                <Metric
                  label="Tokens"
                  value={architecture.total_tokens.toLocaleString()}
                />

                <Metric
                  label="LLM calls"
                  value={architecture.call_count.toString()}
                />

                <Metric
                  label="Latency"
                  value={formatLatency(
                    architecture.latency_ms,
                  )}
                />

                <Metric
                  label="Estimated cost"
                  value={formatCost(
                    architecture.estimated_cost_usd,
                  )}
                />
              </div>

              <details className="answer-details">
                <summary>
                  View answer
                </summary>

                <div className="answer">
                  {architecture.answer}
                </div>
              </details>

              <details className="reasoning-details">
                <summary>
                  Evaluation reasoning
                </summary>

                <div className="reasoning">
                  {evaluation.reasoning}
                </div>
              </details>
            </article>
          );
        })}
      </div>
    </section>
  );
}


function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="metric">
      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>
    </div>
  );
}