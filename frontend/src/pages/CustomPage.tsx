import { useState } from "react";

import { startCustomExperiment } from "../api/client";
import { ArchitecturePicker, RunEstimate } from "../components/RunOptions";
import { navigate } from "../lib/router";
import type { LabConfig } from "../types/experiment";

interface SourceDraft {
  title: string;
  url: string;
  content: string;
}

const emptySource = (): SourceDraft => ({ title: "", url: "", content: "" });

function lines(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.replace(/^[-*•]\s*/, "").trim())
    .filter(Boolean);
}

export default function CustomPage({ config }: { config: LabConfig | null }) {
  const [question, setQuestion] = useState("");
  const [reference, setReference] = useState("");
  const [keyPoints, setKeyPoints] = useState("");
  const [traps, setTraps] = useState("");
  const [difficulty, setDifficulty] = useState("custom");
  const [mode, setMode] = useState<"web" | "manual">(config?.tavily_enabled ? "web" : "manual");
  const [sources, setSources] = useState<SourceDraft[]>([emptySource(), emptySource()]);
  const [trials, setTrials] = useState(1);
  const [architectures, setArchitectures] = useState<string[]>(["1-agent", "2-agent", "3-agent", "4-agent"]);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const updateSource = (index: number, field: keyof SourceDraft, value: string) => {
    setSources(sources.map((source, i) => (i === index ? { ...source, [field]: value } : source)));
  };

  const start = async () => {
    setStarting(true);
    setError(null);

    try {
      const response = await startCustomExperiment({
        question,
        reference_answer: reference.trim() || null,
        key_points: lines(keyPoints),
        must_not_claim: lines(traps),
        difficulty,
        sources_mode: mode,
        sources:
          mode === "manual"
            ? sources
                .filter((source) => source.content.trim())
                .map((source, index) => ({
                  title: source.title.trim() || `Source ${index + 1}`,
                  url: source.url.trim(),
                  content: source.content.trim(),
                }))
            : [],
        trials,
        architectures,
        label: question.slice(0, 80),
      });
      navigate(`/runs/${response.run_id}`);
    } catch (exc) {
      setError((exc as Error).message);
      setStarting(false);
    }
  };

  const valid =
    question.trim().length >= 10 &&
    architectures.length > 0 &&
    (mode === "web" || sources.some((source) => source.content.trim().length >= 10));

  return (
    <main className="app">
      <section className="experiment-header">
        <div className="eyebrow">CUSTOM EXPERIMENT</div>
        <h1>Test your own question</h1>
        <p>
          The evidence is gathered once (web search, or sources you paste) and
          frozen, so every architecture answers from exactly the same material.
          Only the question is required. Key points and trap claims make the
          judging sharper.
        </p>
      </section>

      <section className="panel">
        <label>
          Question
          <textarea
            rows={3}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Example: Is it better to fine-tune a small model or prompt a large one for invoice extraction?"
          />
        </label>

        <div className="form-grid">
          <label>
            Key points a complete answer must contain (optional, one per line)
            <textarea rows={4} value={keyPoints} onChange={(event) => setKeyPoints(event.target.value)} />
          </label>
          <label>
            Trap claims the answer must NOT make (optional, one per line)
            <textarea rows={4} value={traps} onChange={(event) => setTraps(event.target.value)} />
          </label>
        </div>

        <label>
          Reference answer (optional)
          <textarea rows={3} value={reference} onChange={(event) => setReference(event.target.value)} />
        </label>

        <div className="field">
          <span className="field-label">Evidence</span>
          <div className="chip-row">
            <button
              type="button"
              className={mode === "web" ? "chip active" : "chip"}
              disabled={!config?.tavily_enabled}
              onClick={() => setMode("web")}
              title={config?.tavily_enabled ? "" : "Set TAVILY_API_KEY in .env to enable"}
            >
              Search the web (Tavily)
            </button>
            <button
              type="button"
              className={mode === "manual" ? "chip active" : "chip"}
              onClick={() => setMode("manual")}
            >
              Paste my own sources
            </button>
          </div>
        </div>

        {mode === "manual" && (
          <div className="source-editor">
            {sources.map((source, index) => (
              <div className="source-draft" key={index}>
                <div className="form-grid">
                  <input
                    placeholder={`[S${index + 1}] Title`}
                    value={source.title}
                    onChange={(event) => updateSource(index, "title", event.target.value)}
                  />
                  <input
                    placeholder="URL (optional)"
                    value={source.url}
                    onChange={(event) => updateSource(index, "url", event.target.value)}
                  />
                </div>
                <textarea
                  rows={3}
                  placeholder="Source text"
                  value={source.content}
                  onChange={(event) => updateSource(index, "content", event.target.value)}
                />
              </div>
            ))}
            <button type="button" className="ghost-button" onClick={() => setSources([...sources, emptySource()])}>
              + Add source
            </button>
          </div>
        )}

        <div className="form-grid">
          <label>
            Difficulty (for grouping)
            <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
              <option value="custom">Custom</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
              <option value="adversarial">Adversarial</option>
            </select>
          </label>
          <label>
            Trials
            <select value={trials} onChange={(event) => setTrials(Number(event.target.value))}>
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </label>
        </div>

        {config && (
          <>
            <div className="field">
              <span className="field-label">Architectures</span>
              <ArchitecturePicker config={config} value={architectures} onChange={setArchitectures} />
            </div>
            <RunEstimate config={config} architectures={architectures} units={trials} />
          </>
        )}

        {error && <div className="error-box">{error}</div>}

        <button className="primary-button full-width" disabled={!valid || starting} onClick={start}>
          {starting ? "Starting…" : "Run experiment"}
        </button>
      </section>
    </main>
  );
}
