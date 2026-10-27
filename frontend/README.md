# Frontend

React + Vite UI for the agent architecture lab. See the project [README](../README.md).

```bash
npm install
npm run dev     # http://localhost:5173 (proxies /api to the backend on :8000)
npm run build   # type-check + production build
npm run lint
```

| Path | What |
|---|---|
| `src/pages/` | Overview, Benchmark, Custom case, Runs, Run (live progress + results) |
| `src/components/charts.tsx` | Hand-built SVG charts (dot + CI, trade-off scatter, tier lines, bars) |
| `src/components/CaseExplorer.tsx` | Side-by-side answers, judge reasoning, agent traces |
| `src/lib/format.ts` | Architecture colours (validated palette) and formatters |
