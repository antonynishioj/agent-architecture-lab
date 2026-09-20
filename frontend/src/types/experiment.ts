export type ExperimentStatus =
  | "queued"
  | "running"
  | "completed"
  | "completed_with_errors"
  | "failed";

export interface BenchmarkCase {
  case_id: string;
  category: string;
  difficulty: string;
  question: string;
}

export interface BenchmarkListResponse {
  count: number;
  cases: BenchmarkCase[];
}

export interface ExperimentStartResponse {
  run_id: string;
  status: string;
  message: string;
}

export interface ExperimentStatusResponse {
  run_id: string;
  status: ExperimentStatus | string;
  progress: number;
  message: string;
  case_id?: string | null;
  current_case?: string | null;
  current_architecture?: string | null;
  error?: string | null;
}

export interface EvaluationResult {
  answer_relevancy: number;
  completeness: number;
  faithfulness: number;
  overall_quality: number;
  reasoning: string;
}

export interface ArchitectureResult {
  question: string;
  architecture_name: string;
  agent_count: number;
  answer: string;
  model: string;
  call_count: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  latency_ms: number;
  estimated_cost_usd: number | null;
}

export interface EvaluatedArchitectureResult {
  architecture: ArchitectureResult;
  evaluation: EvaluationResult;
}

export interface EvaluatedExperimentResult {
  case_id: string;
  question: string;
  results: EvaluatedArchitectureResult[];
}

export interface ExperimentReport {
  run_id: string;
  experiment: {
    case_id: string;
    question: string;
    research: {
      query: string;
      results: {
        title: string;
        url: string;
        content: string;
        score: number;
      }[];
    };
    results: ArchitectureResult[];
  };
  evaluation: EvaluatedExperimentResult;
}