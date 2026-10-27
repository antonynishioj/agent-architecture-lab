import { useLayoutEffect, useRef, useState, type ReactNode } from "react";

import { colorFor } from "../lib/format";

// Small hand-rolled SVG charts. Specs follow the data-viz rules used
// throughout: 2px lines, ≥8px markers with a 2px surface ring, 4px
// rounded bar ends anchored at the baseline, hairline recessive grid,
// text in text colours (never the series colour), hover tooltips.

const SURFACE = "#111113";
const GRID = "#27272a";
const TEXT_MUTED = "#71717a";
const TEXT_SECONDARY = "#a1a1aa";

interface TooltipState {
  x: number;
  y: number;
  content: ReactNode;
}

function useWidth<T extends HTMLElement>(fallback = 300) {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(fallback);

  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new ResizeObserver(([entry]) => {
      setWidth(Math.max(240, Math.floor(entry.contentRect.width)));
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return [ref, width] as const;
}

function ChartFrame({
  title,
  subtitle,
  children,
  tooltip,
  legend,
  frameRef,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  tooltip: TooltipState | null;
  legend?: string[];
  frameRef: React.RefObject<HTMLDivElement | null>;
}) {
  return (
    <figure className="chart">
      <figcaption>
        <strong>{title}</strong>
        {subtitle && <span>{subtitle}</span>}
      </figcaption>

      {legend && legend.length > 1 && (
        <div className="chart-legend">
          {legend.map((name) => (
            <span key={name}>
              <i style={{ background: colorFor(name) }} />
              {name}
            </span>
          ))}
        </div>
      )}

      <div className="chart-body" ref={frameRef}>
        {children}

        {tooltip && (
          <div
            className="chart-tooltip"
            style={{ left: tooltip.x, top: tooltip.y }}
          >
            {tooltip.content}
          </div>
        )}
      </div>
    </figure>
  );
}

function niceTicks(min: number, max: number, count = 5): number[] {
  const span = max - min || 1;
  const rough = span / count;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => span / s <= count) ?? rough;
  const start = Math.ceil(min / step) * step;
  const ticks = [];

  for (let value = start; value <= max + step * 1e-6; value += step) {
    ticks.push(Number(value.toFixed(6)));
  }

  return ticks;
}

function paddedDomain(values: number[], floor = 0, ceiling = 1): [number, number] {
  if (!values.length) return [floor, ceiling];

  const low = Math.min(...values);
  const high = Math.max(...values);
  const pad = Math.max(0.02, (high - low) * 0.25);

  return [Math.max(floor, low - pad), Math.min(ceiling, high + pad)];
}

function useTooltip() {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const show = (event: React.PointerEvent, content: ReactNode) => {
    const box = (event.currentTarget as SVGElement).ownerSVGElement?.getBoundingClientRect();
    if (!box) return;

    setTooltip({
      x: event.clientX - box.left + 14,
      y: event.clientY - box.top + 14,
      content,
    });
  };

  return { tooltip, show, hide: () => setTooltip(null) };
}

// ---------------------------------------------------------------------------
// Dot + whisker: mean with 95% CI per architecture. Quality scores bunch
// near the top of the scale, so a dot plot on a zoomed axis shows the
// differences honestly where a zero-based bar would hide them.

export interface IntervalDatum {
  name: string;
  value: number | null;
  low: number | null;
  high: number | null;
  detail?: string;
}

export function IntervalChart({
  title,
  subtitle,
  data,
}: {
  title: string;
  subtitle?: string;
  data: IntervalDatum[];
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const { tooltip, show, hide } = useTooltip();

  const rows = data.filter((d) => d.value !== null);
  const values = rows.flatMap((d) => [d.low ?? d.value!, d.high ?? d.value!]);
  const [min, max] = paddedDomain(values);

  const margin = { top: 8, right: 56, bottom: 28, left: 72 };
  const rowHeight = 40;
  const height = margin.top + margin.bottom + rows.length * rowHeight;
  const plotWidth = width - margin.left - margin.right;
  const x = (value: number) => margin.left + ((value - min) / (max - min)) * plotWidth;

  return (
    <ChartFrame title={title} subtitle={subtitle} tooltip={tooltip} frameRef={ref}>
      <svg width={width} height={height} role="img" aria-label={title}>
        {niceTicks(min, max).map((tick) => (
          <g key={tick}>
            <line x1={x(tick)} x2={x(tick)} y1={margin.top} y2={height - margin.bottom} stroke={GRID} />
            <text x={x(tick)} y={height - 8} fill={TEXT_MUTED} fontSize={11} textAnchor="middle">
              {tick.toFixed(2)}
            </text>
          </g>
        ))}

        {rows.map((d, index) => {
          const cy = margin.top + index * rowHeight + rowHeight / 2;
          const content = (
            <>
              <b>{d.name}</b>
              <div>Mean {d.value!.toFixed(3)}</div>
              <div>95% CI {d.low?.toFixed(3)} – {d.high?.toFixed(3)}</div>
              {d.detail && <div>{d.detail}</div>}
            </>
          );

          return (
            <g key={d.name} onPointerMove={(e) => show(e, content)} onPointerLeave={hide}>
              <rect x={0} y={cy - rowHeight / 2} width={width} height={rowHeight} fill="transparent" />
              <text x={margin.left - 12} y={cy + 4} fill={TEXT_SECONDARY} fontSize={13} textAnchor="end">
                {d.name}
              </text>
              {d.low !== null && d.high !== null && (
                <line x1={x(d.low)} x2={x(d.high)} y1={cy} y2={cy} stroke={colorFor(d.name)} strokeWidth={2} strokeLinecap="round" />
              )}
              <circle cx={x(d.value!)} cy={cy} r={6} fill={colorFor(d.name)} stroke={SURFACE} strokeWidth={2} />
              <text x={x(d.high ?? d.value!) + 10} y={cy + 4} fill={TEXT_SECONDARY} fontSize={12}>
                {d.value!.toFixed(3)}
              </text>
            </g>
          );
        })}
      </svg>
    </ChartFrame>
  );
}

// ---------------------------------------------------------------------------
// Horizontal bars for magnitudes that start at zero (tokens, latency).

export function BarChart({
  title,
  subtitle,
  data,
  format,
}: {
  title: string;
  subtitle?: string;
  data: { name: string; value: number | null }[];
  format: (value: number) => string;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const { tooltip, show, hide } = useTooltip();

  const rows = data.filter((d) => d.value !== null) as { name: string; value: number }[];
  const max = Math.max(1, ...rows.map((d) => d.value));

  const margin = { top: 4, right: 70, bottom: 8, left: 72 };
  const rowHeight = 34;
  const barHeight = 18;
  const height = margin.top + margin.bottom + rows.length * rowHeight;
  const plotWidth = width - margin.left - margin.right;

  return (
    <ChartFrame title={title} subtitle={subtitle} tooltip={tooltip} frameRef={ref}>
      <svg width={width} height={height} role="img" aria-label={title}>
        <line x1={margin.left} x2={margin.left} y1={margin.top} y2={height - margin.bottom} stroke={GRID} />

        {rows.map((d, index) => {
          const y = margin.top + index * rowHeight + (rowHeight - barHeight) / 2;
          const length = Math.max(2, (d.value / max) * plotWidth);
          const radius = Math.min(4, length / 2);

          return (
            <g key={d.name} onPointerMove={(e) => show(e, <><b>{d.name}</b><div>{format(d.value)}</div></>)} onPointerLeave={hide}>
              <rect x={0} y={y - 8} width={width} height={barHeight + 16} fill="transparent" />
              <text x={margin.left - 12} y={y + barHeight / 2 + 4} fill={TEXT_SECONDARY} fontSize={13} textAnchor="end">
                {d.name}
              </text>
              {/* Square at the baseline, 4px rounded at the data end. */}
              <path
                d={`M${margin.left},${y} h${length - radius} a${radius},${radius} 0 0 1 ${radius},${radius} v${barHeight - 2 * radius} a${radius},${radius} 0 0 1 -${radius},${radius} h-${length - radius} z`}
                fill={colorFor(d.name)}
              />
              <text x={margin.left + length + 8} y={y + barHeight / 2 + 4} fill={TEXT_SECONDARY} fontSize={12}>
                {format(d.value)}
              </text>
            </g>
          );
        })}
      </svg>
    </ChartFrame>
  );
}

// ---------------------------------------------------------------------------
// Quality vs cost scatter: the trade-off in one picture. Every dot is
// direct-labelled, so identity never relies on colour alone.

export function TradeoffChart({
  title,
  subtitle,
  data,
}: {
  title: string;
  subtitle?: string;
  data: { name: string; tokens: number | null; quality: number | null }[];
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const { tooltip, show, hide } = useTooltip();

  const points = data.filter((d) => d.tokens !== null && d.quality !== null) as {
    name: string;
    tokens: number;
    quality: number;
  }[];

  const margin = { top: 16, right: 80, bottom: 40, left: 52 };
  const height = 280;
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;

  const maxTokens = Math.max(1, ...points.map((p) => p.tokens)) * 1.1;
  const [qMin, qMax] = paddedDomain(points.map((p) => p.quality));

  const x = (value: number) => margin.left + (value / maxTokens) * plotWidth;
  const y = (value: number) => margin.top + (1 - (value - qMin) / (qMax - qMin)) * plotHeight;

  return (
    <ChartFrame title={title} subtitle={subtitle} tooltip={tooltip} frameRef={ref}>
      <svg width={width} height={height} role="img" aria-label={title}>
        {niceTicks(qMin, qMax, 4).map((tick) => (
          <g key={`y${tick}`}>
            <line x1={margin.left} x2={width - margin.right} y1={y(tick)} y2={y(tick)} stroke={GRID} />
            <text x={margin.left - 8} y={y(tick) + 4} fill={TEXT_MUTED} fontSize={11} textAnchor="end">
              {tick.toFixed(2)}
            </text>
          </g>
        ))}

        {niceTicks(0, maxTokens, 5).map((tick) => (
          <text key={`x${tick}`} x={x(tick)} y={height - 20} fill={TEXT_MUTED} fontSize={11} textAnchor="middle">
            {tick >= 1000 ? `${tick / 1000}K` : tick}
          </text>
        ))}

        <text x={margin.left + plotWidth / 2} y={height - 4} fill={TEXT_MUTED} fontSize={11} textAnchor="middle">
          Tokens per answer (lower is cheaper) →
        </text>

        {points.map((p) => (
          <g
            key={p.name}
            onPointerMove={(e) => show(e, <><b>{p.name}</b><div>Quality {p.quality.toFixed(3)}</div><div>{Math.round(p.tokens).toLocaleString()} tokens</div></>)}
            onPointerLeave={hide}
          >
            <circle cx={x(p.tokens)} cy={y(p.quality)} r={14} fill="transparent" />
            <circle cx={x(p.tokens)} cy={y(p.quality)} r={6} fill={colorFor(p.name)} stroke={SURFACE} strokeWidth={2} />
            <text x={x(p.tokens) + 11} y={y(p.quality) + 4} fill={TEXT_SECONDARY} fontSize={12}>
              {p.name}
            </text>
          </g>
        ))}
      </svg>
    </ChartFrame>
  );
}

// ---------------------------------------------------------------------------
// Quality by difficulty tier, one line per architecture.

export function TierChart({
  title,
  subtitle,
  tiers,
  series,
}: {
  title: string;
  subtitle?: string;
  tiers: string[];
  series: { name: string; values: (number | null)[] }[];
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const { tooltip, show, hide } = useTooltip();

  const margin = { top: 16, right: 24, bottom: 32, left: 52 };
  const height = 280;
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;

  const values = series.flatMap((s) => s.values.filter((v): v is number => v !== null));
  const [min, max] = paddedDomain(values);

  const step = tiers.length > 1 ? plotWidth / (tiers.length - 1) : 0;
  const x = (index: number) => margin.left + (tiers.length > 1 ? index * step : plotWidth / 2);
  const y = (value: number) => margin.top + (1 - (value - min) / (max - min)) * plotHeight;

  return (
    <ChartFrame
      title={title}
      subtitle={subtitle}
      tooltip={tooltip}
      legend={series.map((s) => s.name)}
      frameRef={ref}
    >
      <svg width={width} height={height} role="img" aria-label={title}>
        {niceTicks(min, max, 4).map((tick) => (
          <g key={tick}>
            <line x1={margin.left} x2={width - margin.right} y1={y(tick)} y2={y(tick)} stroke={GRID} />
            <text x={margin.left - 8} y={y(tick) + 4} fill={TEXT_MUTED} fontSize={11} textAnchor="end">
              {tick.toFixed(2)}
            </text>
          </g>
        ))}

        {tiers.map((tier, index) => (
          <text key={tier} x={x(index)} y={height - 10} fill={TEXT_SECONDARY} fontSize={12} textAnchor="middle">
            {tier}
          </text>
        ))}

        {series.map((s) => {
          const points = s.values
            .map((value, index) => (value === null ? null : [x(index), y(value)]))
            .filter((point): point is number[] => point !== null);

          return (
            <g key={s.name}>
              <polyline
                points={points.map((point) => point.join(",")).join(" ")}
                fill="none"
                stroke={colorFor(s.name)}
                strokeWidth={2}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
              {s.values.map((value, index) =>
                value === null ? null : (
                  <g
                    key={index}
                    onPointerMove={(e) => show(e, <><b>{s.name}</b><div>{tiers[index]}: {value.toFixed(3)}</div></>)}
                    onPointerLeave={hide}
                  >
                    <circle cx={x(index)} cy={y(value)} r={12} fill="transparent" />
                    <circle cx={x(index)} cy={y(value)} r={4.5} fill={colorFor(s.name)} stroke={SURFACE} strokeWidth={2} />
                  </g>
                ),
              )}
            </g>
          );
        })}
      </svg>
    </ChartFrame>
  );
}
