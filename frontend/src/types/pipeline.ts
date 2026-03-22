export interface Pipeline {
  id: string;
  name: string;
  description: string | null;
  dataset_id: string | null;
  is_active: boolean;
  step_count: number;
  created_at: string;
  updated_at: string;
}

export interface PipelineStep {
  id: string;
  pipeline_id: string;
  script_version_id: string;
  step_order: number;
  step_name: string;
  timeout_seconds: number;
  retry_count: number;
  created_at: string;
}

export interface PipelineRun {
  id: string;
  pipeline_id: string;
  environment: string;
  status: string;
  triggered_by: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  env_snapshot: Record<string, unknown>;
  created_at: string;
}

export interface PipelineRunStepLog {
  id: string;
  pipeline_run_id: string;
  step_id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  log_output: string | null;
  rows_affected: number | null;
  error_message: string | null;
  created_at: string;
}
