import { estimateRun } from "../lib/estimate";
import { colorFor, minutes } from "../lib/format";
import type { LabConfig } from "../types/experiment";

export function ArchitecturePicker({
  config,
  value,
  onChange,
}: {
  config: LabConfig;
  value: string[];
  onChange: (next: string[]) => void;
}) {
  return (
    <div className="chip-row">
      {config.architectures.map((architecture) => {
        const active = value.includes(architecture.name);

        return (
          <button
            key={architecture.name}
            type="button"
            className={active ? "chip active" : "chip"}
            onClick={() =>
              onChange(
                active
                  ? value.filter((name) => name !== architecture.name)
                  : [...value, architecture.name],
              )
            }
          >
            <i className="swatch" style={{ background: colorFor(architecture.name) }} />
            {architecture.name}
          </button>
        );
      })}
    </div>
  );
}

export function RunEstimate({
  config,
  architectures,
  units,
}: {
  config: LabConfig;
  architectures: string[];
  units: number;
}) {
  const estimate = estimateRun(config, architectures, units);

  return (
    <div className={estimate.fitsToday ? "estimate" : "estimate over"}>
      <div>
        <span>Generator calls</span>
        <strong>{estimate.generatorCalls}</strong>
        <small>{Math.max(0, estimate.generatorLeft)} left today</small>
      </div>
      <div>
        <span>Judge calls</span>
        <strong>{estimate.judgeCalls}</strong>
        <small>{Math.max(0, estimate.judgeLeft)} left today</small>
      </div>
      <div>
        <span>Estimated time</span>
        <strong>≈ {minutes(estimate.seconds)}</strong>
        <small>keep the backend running</small>
      </div>
      {!estimate.fitsToday && (
        <p>
          This exceeds today's remaining quota. You can still start it: the run
          pauses when the quota runs out and resumes tomorrow without repeating
          finished calls.
        </p>
      )}
    </div>
  );
}
