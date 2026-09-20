import { useState } from "react";
import "./App.css";

type Mode = "home" | "benchmark" | "custom";

function App() {
  const [mode, setMode] = useState<Mode>("home");

  if (mode === "benchmark") {
    return (
      <BenchmarkPage
        onBack={() => setMode("home")}
      />
    );
  }

  if (mode === "custom") {
    return (
      <CustomCasePage
        onBack={() => setMode("home")}
      />
    );
  }

  return (
    <main className="app">
      <section className="hero">
        <div className="eyebrow">
          AI AGENT ARCHITECTURE LAB
        </div>

        <h1>
          How many AI agents
          <span> do you actually need?</span>
        </h1>

        <p className="hero-description">
          An experimental framework for measuring how
          agent specialization affects answer quality,
          cost, latency, token usage, and reliability.
        </p>

        <div className="hero-actions">
          <button
            className="primary-button"
            onClick={() => setMode("benchmark")}
          >
            Run Benchmark
          </button>

          <button
            className="secondary-button"
            onClick={() => setMode("custom")}
          >
            Test Your Own Case
          </button>
        </div>
      </section>

      <section className="architecture-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">
              EXPERIMENT DESIGN
            </div>

            <h2>
              Four independent architectures
            </h2>
          </div>

          <p>
            Every architecture receives the same question
            and the same frozen research evidence.
          </p>
        </div>

        <div className="architecture-grid">
          <ArchitectureCard
            number="01"
            title="1 Agent"
            description="One agent handles research, fact checking, criticism, and writing."
          />

          <ArchitectureCard
            number="02"
            title="2 Agents"
            description="Research + fact checking, followed by criticism + writing."
          />

          <ArchitectureCard
            number="03"
            title="3 Agents"
            description="Research, fact checking + criticism, followed by writing."
          />

          <ArchitectureCard
            number="04"
            title="4 Agents"
            description="Research, fact checking, criticism, and writing are separated."
          />
        </div>
      </section>

      <section className="metrics-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">
              MEASUREMENTS
            </div>

            <h2>
              No single winner
            </h2>
          </div>

          <p>
            The experiment reports separate measurements
            instead of collapsing everything into one score.
          </p>
        </div>

        <div className="metrics-grid">
          <MetricCard
            title="Answer Quality"
            description="Relevancy, completeness, faithfulness, and overall quality."
          />

          <MetricCard
            title="Token Usage"
            description="Input, output, and total tokens consumed."
          />

          <MetricCard
            title="Latency"
            description="Time spent executing each architecture."
          />

          <MetricCard
            title="Cost"
            description="Estimated model cost based on token usage and configured pricing."
          />
        </div>
      </section>

      <footer>
        <span>
          AI Agent Architecture Lab
        </span>

        <span>
          Experimental project
        </span>
      </footer>
    </main>
  );
}


function ArchitectureCard({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <article className="architecture-card">
      <div className="card-number">
        {number}
      </div>

      <h3>{title}</h3>

      <p>{description}</p>
    </article>
  );
}


function MetricCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <article className="metric-card">
      <h3>{title}</h3>

      <p>{description}</p>
    </article>
  );
}


function BenchmarkPage({
  onBack,
}: {
  onBack: () => void;
}) {
  return (
    <main className="app">
      <button
        className="back-button"
        onClick={onBack}
      >
        ← Back
      </button>

      <section className="experiment-header">
        <div className="eyebrow">
          BENCHMARK
        </div>

        <h1>
          Run the predefined benchmark
        </h1>

        <p>
          The benchmark uses the frozen research
          dataset and evaluates all four architectures
          independently.
        </p>
      </section>

      <section className="experiment-panel">
        <div className="panel-header">
          <div>
            <span className="panel-label">
              BENCHMARK CASES
            </span>

            <h2>
              Ready to run
            </h2>
          </div>

          <span className="status-badge">
            3 cases
          </span>
        </div>

        <div className="case-list">
          <div className="case-row">
            <span>RAG</span>
            <strong>
              RAG benefits
            </strong>
            <span>Easy</span>
          </div>

          <div className="case-row">
            <span>RAG</span>
            <strong>
              RAG reliability
            </strong>
            <span>Medium</span>
          </div>

          <div className="case-row">
            <span>AI System Design</span>
            <strong>
              In-house vs external AI
            </strong>
            <span>Medium</span>
          </div>
        </div>

        <button className="primary-button full-width">
          Start Benchmark
        </button>
      </section>
    </main>
  );
}


function CustomCasePage({
  onBack,
}: {
  onBack: () => void;
}) {
  return (
    <main className="app">
      <button
        className="back-button"
        onClick={onBack}
      >
        ← Back
      </button>

      <section className="experiment-header">
        <div className="eyebrow">
          CUSTOM EXPERIMENT
        </div>

        <h1>
          Test your own research question
        </h1>

        <p>
          Provide a question and reference answer.
          The system will retrieve evidence once and
          give the same frozen evidence to all four
          architectures.
        </p>
      </section>

      <section className="experiment-panel">
        <label>
          Question
          <textarea
            placeholder="Example: What are the main advantages of retrieval augmented generation?"
            rows={5}
          />
        </label>

        <label>
          Reference answer
          <textarea
            placeholder="Provide the answer that should be used as the evaluation reference."
            rows={7}
          />
        </label>

        <div className="form-grid">
          <label>
            Category
            <input
              placeholder="Custom"
            />
          </label>

          <label>
            Difficulty
            <select defaultValue="custom">
              <option value="custom">
                Custom
              </option>
              <option value="easy">
                Easy
              </option>
              <option value="medium">
                Medium
              </option>
              <option value="hard">
                Hard
              </option>
            </select>
          </label>
        </div>

        <button className="primary-button full-width">
          Run Experiment
        </button>
      </section>
    </main>
  );
}


export default App;