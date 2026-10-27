import { navigate } from "../lib/router";
import { colorFor } from "../lib/format";
import type { LabConfig } from "../types/experiment";
import QuotaCard from "../components/QuotaCard";

export default function HomePage({ config }: { config: LabConfig | null }) {
  return (
    <main className="app">
      <section className="hero">
        <div className="eyebrow">AI AGENT ARCHITECTURE LAB</div>

        <h1>
          How many AI agents
          <span> do you actually need?</span>
        </h1>

        <p className="hero-description">
          The same four jobs (research, fact-checking, critique, writing) split
          across 1, 2, 3 or 4 agents. Same model, same evidence, same
          instructions. Only the number of agents changes. A blind judge scores
          every answer, and a rule fixed in advance picks the winner.
        </p>

        <div className="hero-actions">
          <button className="primary-button" onClick={() => navigate("/benchmark")}>
            Run the benchmark
          </button>
          <button className="secondary-button" onClick={() => navigate("/custom")}>
            Test your own question
          </button>
          <button className="ghost-button" onClick={() => navigate("/runs")}>
            View past runs →
          </button>
        </div>
      </section>

      {config && <QuotaCard config={config} />}

      <section className="architecture-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">THE INDEPENDENT VARIABLE</div>
            <h2>Four architectures, four roles each</h2>
          </div>
          <p>
            Every architecture runs all four roles using identical role
            instructions. Agents that research or fact-check see the sources.
            Every agent sees all earlier agents' notes.
          </p>
        </div>

        <div className="architecture-grid">
          {(config?.architectures ?? []).map((architecture) => (
            <article className="architecture-card" key={architecture.name}>
              <div className="card-number">
                <i className="swatch" style={{ background: colorFor(architecture.name) }} />
                {architecture.name}
              </div>

              <div className="agent-chain">
                {architecture.agents.map((roles, index) => (
                  <div className="agent-box" key={index}>
                    <span>Agent {index + 1}</span>
                    {roles.join(" + ")}
                  </div>
                ))}
              </div>

              <p>
                {architecture.calls_per_case.generator} LLM call
                {architecture.calls_per_case.generator > 1 ? "s" : ""} per answer
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="metrics-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">HOW THE WINNER IS CHOSEN</div>
            <h2>The smallest team that is not measurably worse</h2>
          </div>
          <p>
            Quality alone would always favour the biggest team if it won by
            noise. Cost alone would always favour one agent. The rule combines
            them, and it was fixed before any data came in.
          </p>
        </div>

        <div className="metrics-grid">
          <article className="metric-card">
            <h3>1 · Measure quality</h3>
            <p>
              A blind judge scores relevancy, completeness (key-point checklist),
              faithfulness, citations, uncertainty handling and overall quality.
              The Quality Index is their mean.
            </p>
          </article>
          <article className="metric-card">
            <h3>2 · Find the best</h3>
            <p>
              The architecture with the highest mean Quality Index across cases,
              with each case averaged over 3 trials.
            </p>
          </article>
          <article className="metric-card">
            <h3>3 · Test for ties</h3>
            <p>
              A paired bootstrap over cases checks whether each other
              architecture is significantly worse than the best, or within 0.02.
            </p>
          </article>
          <article className="metric-card">
            <h3>4 · Prefer the cheaper</h3>
            <p>
              Among those tied with the best, the one using the fewest tokens
              wins. Results are also reported per difficulty tier.
            </p>
          </article>
        </div>
      </section>

      <footer>
        <span>AI Agent Architecture Lab</span>
        <span>
          Generator {config?.generator_model ?? "…"} · Judge {config?.judge_model ?? "…"}
        </span>
      </footer>
    </main>
  );
}
