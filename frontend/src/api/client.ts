import type {
  BenchmarkListResponse,
  ExperimentStartResponse,
  JobStatus,
  LabConfig,
  RunDetail,
  RunListItem,
  Summary,
} from "../types/experiment";

// Empty by default: the Vite dev server proxies /api to the backend.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

function wsBaseUrl(): string {
  if (import.meta.env.VITE_WS_BASE_URL) {
    return import.meta.env.VITE_WS_BASE_URL;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}`;
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const data = await response.json();

      if (typeof data?.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data?.detail)) {
        message = data.detail
          .map((item: { loc?: string[]; msg?: string }) =>
            `${(item.loc || []).slice(1).join(".")}: ${item.msg}`,
          )
          .join("; ");
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}

export function getConfig(): Promise<LabConfig> {
  return request<LabConfig>("/api/config");
}

export function getBenchmarks(): Promise<BenchmarkListResponse> {
  return request<BenchmarkListResponse>("/api/benchmarks");
}

export interface BenchmarkRunInput {
  case_ids: string[];
  trials: number;
  architectures: string[];
  label: string;
}

export function startBenchmark(
  input: BenchmarkRunInput,
): Promise<ExperimentStartResponse> {
  return request<ExperimentStartResponse>("/api/experiments/benchmark", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export interface CustomExperimentInput {
  question: string;
  reference_answer: string | null;
  key_points: string[];
  must_not_claim: string[];
  difficulty: string;
  sources_mode: "web" | "manual";
  sources: { title: string; url: string; content: string }[];
  trials: number;
  architectures: string[];
  label: string;
}

export function startCustomExperiment(
  input: CustomExperimentInput,
): Promise<ExperimentStartResponse> {
  return request<ExperimentStartResponse>("/api/experiments/custom", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getStatus(runId: string): Promise<JobStatus> {
  return request<JobStatus>(`/api/experiments/${runId}/status`);
}

export function listRuns(): Promise<RunListItem[]> {
  return request<RunListItem[]>("/api/runs");
}

export function getRun(runId: string): Promise<RunDetail> {
  return request<RunDetail>(`/api/runs/${runId}`);
}

export function getSummary(runId: string): Promise<Summary> {
  return request<Summary>(`/api/runs/${runId}/summary`);
}

export function resumeRun(runId: string): Promise<ExperimentStartResponse> {
  return request<ExperimentStartResponse>(`/api/runs/${runId}/resume`, {
    method: "POST",
  });
}

export function csvUrl(runId: string): string {
  return `${API_BASE_URL}/api/runs/${runId}/export.csv`;
}

export function openProgressSocket(runId: string): WebSocket {
  return new WebSocket(`${wsBaseUrl()}/api/ws/experiments/${runId}`);
}
