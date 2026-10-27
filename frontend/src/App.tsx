import { useEffect, useState } from "react";

import "./App.css";
import { getConfig } from "./api/client";
import { navigate, useRoute } from "./lib/router";
import BenchmarkPage from "./pages/BenchmarkPage";
import CustomPage from "./pages/CustomPage";
import HomePage from "./pages/HomePage";
import RunPage from "./pages/RunPage";
import RunsPage from "./pages/RunsPage";
import type { LabConfig } from "./types/experiment";

const NAV = [
  { path: "/", page: "home", label: "Overview" },
  { path: "/benchmark", page: "benchmark", label: "Benchmark" },
  { path: "/custom", page: "custom", label: "Custom case" },
  { path: "/runs", page: "runs", label: "Runs" },
] as const;

function App() {
  const route = useRoute();
  const [config, setConfig] = useState<LabConfig | null>(null);
  const [offline, setOffline] = useState(false);

  // Re-read the config (quota usage, active run) on every navigation.
  useEffect(() => {
    getConfig()
      .then((next) => {
        setConfig(next);
        setOffline(false);
      })
      .catch(() => setOffline(true));
  }, [route]);

  const activePage = route.page === "run" ? "runs" : route.page;

  return (
    <>
      <nav className="topbar">
        <button className="brand" onClick={() => navigate("/")}>
          Agent Architecture Lab
        </button>

        <div className="nav-links">
          {NAV.map((item) => (
            <button
              key={item.page}
              className={activePage === item.page ? "nav-link active" : "nav-link"}
              onClick={() => navigate(item.path)}
            >
              {item.label}
            </button>
          ))}
        </div>

        {config?.active_run && route.page !== "run" && (
          <button className="live-pill" onClick={() => navigate(`/runs/${config.active_run}`)}>
            <span className="pulse" /> Run in progress
          </button>
        )}
      </nav>

      {offline && (
        <div className="app">
          <div className="error-box">
            Can't reach the backend. Start it with <code>uv run agent-lab serve</code> in the
            project folder, then reload this page.
          </div>
        </div>
      )}

      {route.page === "home" && <HomePage config={config} />}
      {route.page === "benchmark" && <BenchmarkPage config={config} />}
      {route.page === "custom" && <CustomPage config={config} />}
      {route.page === "runs" && <RunsPage />}
      {route.page === "run" && <RunPage key={route.runId} runId={route.runId} />}
    </>
  );
}

export default App;
