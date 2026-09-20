import type {
  BenchmarkListResponse,
  ExperimentReport,
  ExperimentStartResponse,
  ExperimentStatusResponse,
} from "../types/experiment";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";

const WS_BASE_URL =
  import.meta.env.VITE_WS_BASE_URL ||
  "ws://localhost:8000";


async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    },
  );

  if (!response.ok) {
    let message =
      `Request failed with status ${response.status}`;

    try {
      const data = await response.json();

      if (data?.detail) {
        message = data.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}


export async function getBenchmarks(): Promise<BenchmarkListResponse> {
  return request<BenchmarkListResponse>(
    "/api/benchmarks",
  );
}


export async function startBenchmark(): Promise<ExperimentStartResponse> {
  return request<ExperimentStartResponse>(
    "/api/experiments/benchmark",
    {
      method: "POST",
    },
  );
}


export interface CustomExperimentInput {
  question: string;
  reference_answer: string;
  category: string;
  difficulty: string;
}


export async function startCustomExperiment(
  input: CustomExperimentInput,
): Promise<ExperimentStartResponse> {
  return request<ExperimentStartResponse>(
    "/api/experiments/custom",
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}


export async function getExperimentStatus(
  runId: string,
): Promise<ExperimentStatusResponse> {
  return request<ExperimentStatusResponse>(
    `/api/experiments/${runId}/status`,
  );
}


export async function getExperimentResults(
  runId: string,
): Promise<ExperimentReport> {
  return request<ExperimentReport>(
    `/api/experiments/${runId}`,
  );
}


export function createExperimentWebSocket(
  runId: string,
): WebSocket {
  return new WebSocket(
    `${WS_BASE_URL}/api/ws/experiments/${runId}`,
  );
}