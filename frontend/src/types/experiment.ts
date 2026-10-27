export type RunStatus =
  | "queued"
  | "running"
  | "paused"
  | "completed"
  | "completed_with_errors"
  | "failed"
  | "not_found";

export interface ArchitectureInfo {
  name: string;
  agent_count: number;
  description: string;
  agents: string[][];
  calls_per_case: { generator: number; judge: number };
}

export interface LabConfig {
  generator_model: string;
  judge_model: string;
  generator_rpm: number;
  judge_rpm: number;
  generator_rpd: number;
  judge_rpd: number;
  api_key_configured: boolean;
  tavily_enabled: boolean;
  usage_today: Record<string, number>;
  active_run: string | null;
  architectures: ArchitectureInfo[];
}

export interface BenchmarkCase {
  case_id: string;
  category: string;
  difficulty: string;
  question: string;
  design_notes: string;
  key_points: number;
  sources: number;
}

export interface BenchmarkListResponse {
  version: string;
  cases: BenchmarkCase[];
}

export interface ExperimentStartResponse {
  run_id: string;
  status: string;
  message: string;
}

export interface JobEvent {
  time: string;
  stage: string | null;
  message: string;
}

export interface JobStatus {
  run_id: string;
  status: RunStatus | string;
  progress: number;
  message: string;
  current_case?: string | null;
  current_trial?: number | null;
  current_architecture?: string | null;
  error?: string | null;
  events: JobEvent[];
}

export interface RunListItem {
  run_id: string;
  directory: string;
  run_type: string;
  label: string;
  status: RunStatus | string;
  created_at: string;
  trials: number;
  case_count: number;
  architectures: string[];
  completed_items: number;
  failed_items: number;
  total_items: number;
  generator_model: string;
  error: string | null;
}

export interface Source {
  title: string;
  url: string;
  content: string;
  score: number;
  published?: string | null;
}

export interface CaseDefinition {
  case_id: string;
  question: string;
  reference_answer: string | null;
  category: string;
  difficulty: string;
  key_points: string[];
  must_not_claim: string[];
  design_notes: string;
  source_kind: string;
  research: { query: string; results: Source[] } | null;
}

export interface AgentStep {
  agent_index: number;
  roles: string[];
  output: string;
  input_tokens: number;
  output_tokens: number;
  thinking_tokens: number;
  latency_ms: number;
  saw_sources: boolean;
}

export interface Evaluation {
  answer_relevancy: number;
  completeness: number;
  faithfulness: number;
  citation_quality: number;
  uncertainty_handling: number;
  overall_quality: number;
  judge_completeness: number | null;
  key_points: { point: string; status: string }[];
  unsupported_claims: string[];
  trap_violations: string[];
  reasoning: string;
}

export interface Outcome {
  architecture: string;
  agent_count: number;
  status: string;
  error: string | null;
  answer: string;
  steps: AgentStep[];
  call_count: number;
  input_tokens: number;
  output_tokens: number;
  thinking_tokens: number;
  total_tokens: number;
  latency_ms: number;
  retries: number;
  estimated_cost_usd: number | null;
  evaluation: Evaluation | null;
  judge_error: string | null;
  deterministic: {
    word_count: number;
    citation_count: number;
    distinct_sources_cited: number;
    invalid_citations: number;
    citation_validity: number;
    sentence_citation_coverage: number;
  } | null;
}

export interface CaseTrialResult {
  case_id: string;
  trial: number;
  difficulty: string;
  category: string;
  question: string;
  outcomes: Outcome[];
  ranking: {
    order: string[];
    labels: Record<string, string>;
    reasoning: string;
  } | null;
  ranking_error: string | null;
}

export interface RunManifest {
  run_id: string;
  directory: string;
  run_type: string;
  label: string;
  status: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
  generator_model: string;
  judge_model: string;
  trials: number;
  architectures: string[];
  case_ids: string[];
  prompt_fingerprint: string;
  git_commit: string | null;
  items: { case_id: string; trial: number; status: string; error: string | null }[];
}

export interface RunDetail {
  manifest: RunManifest;
  cases: CaseDefinition[];
  items: CaseTrialResult[];
}

export interface ArchitectureRow {
  architecture: string;
  agent_count: number;
  units_completed: number;
  units_failed: number;
  cases_scored: number;
  quality_index: number | null;
  quality_ci_low: number | null;
  quality_ci_high: number | null;
  dimensions: Record<string, number | null>;
  trap_violation_rate: number | null;
  unsupported_claims_per_answer: number | null;
  citation_validity: number | null;
  sentence_citation_coverage: number | null;
  word_count: number | null;
  win_rate: number | null;
  mean_rank: number | null;
  calls_per_answer: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  thinking_tokens: number | null;
  total_tokens: number | null;
  latency_s: number | null;
  estimated_cost_usd: number | null;
  retries: number;
  quality_per_1k_tokens: number | null;
}

export interface Comparison {
  architecture: string;
  versus: string;
  n_cases: number;
  diff_mean: number | null;
  ci_low: number | null;
  ci_high: number | null;
  as_good_as_best: boolean;
}

export interface Summary {
  run_id: string;
  status: string;
  config: {
    generator_model: string;
    judge_model: string;
    trials: number;
    architectures: string[];
    cases_planned: number;
    units_planned: number;
    units_completed: number;
    prompt_fingerprint: string;
    git_commit: string | null;
  };
  winner: {
    winner: string | null;
    best_quality: string | null;
    candidates: string[];
    comparisons: Comparison[];
    rule: string;
    explanation: string;
  };
  architectures: ArchitectureRow[];
  by_difficulty: Record<
    string,
    {
      cases: number;
      quality_index: Record<string, number | null>;
      best_quality: string | null;
      winner: string | null;
    }
  >;
  sensitivity: Record<string, { best_quality: string | null; winner: string | null }>;
  per_case: {
    case_id: string;
    difficulty: string;
    trials: number;
    quality_index: Record<string, number | null>;
  }[];
}
