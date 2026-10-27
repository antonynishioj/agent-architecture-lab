import type { LabConfig } from "../types/experiment";

function Meter({
  label,
  model,
  used,
  limit,
  rpm,
}: {
  label: string;
  model: string;
  used: number;
  limit: number;
  rpm: number;
}) {
  const share = Math.min(1, used / Math.max(1, limit));
  const level = share > 0.9 ? "danger" : share > 0.7 ? "warning" : "ok";

  return (
    <div className="quota-meter">
      <div className="quota-head">
        <span>
          {label} <code>{model}</code>
        </span>
        <strong>
          {used} / {limit} today
        </strong>
      </div>
      <div className={`meter-track ${level}`}>
        <div className="meter-fill" style={{ width: `${share * 100}%` }} />
      </div>
      <span className="muted small-text">
        Rate-limited to {rpm} requests/min · quota resets at midnight Pacific
      </span>
    </div>
  );
}

export default function QuotaCard({ config }: { config: LabConfig }) {
  const usage = config.usage_today;

  return (
    <section className="panel quota-card">
      <div className="panel-header">
        <div>
          <span className="panel-label">GEMINI FREE TIER · TODAY'S USAGE</span>
          <h2>Request budget</h2>
        </div>
        {!config.api_key_configured && (
          <span className="status-badge danger">GEMINI_API_KEY missing</span>
        )}
      </div>

      <div className="quota-grid">
        <Meter
          label="Generator"
          model={config.generator_model}
          used={usage[config.generator_model] ?? 0}
          limit={config.generator_rpd}
          rpm={config.generator_rpm}
        />
        {config.judge_model !== config.generator_model && (
          <Meter
            label="Judge"
            model={config.judge_model}
            used={usage[config.judge_model] ?? 0}
            limit={config.judge_rpd}
            rpm={config.judge_rpm}
          />
        )}
      </div>

      <p className="muted small-text">
        Counts are tracked locally and include retries. Daily limits are
        estimates set in <code>.env</code> (GEMINI_RPD, GEMINI_JUDGE_RPD). Check
        your project's real limits at aistudio.google.com/rate-limit.
      </p>
    </section>
  );
}
