export interface AlarmRule {
  id: string;
  pipeline_id: string;
  name: string;
  metric_name: string;
  condition: string;
  threshold: number;
  lookback_runs: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlarmEvent {
  id: string;
  alarm_rule_id: string;
  pipeline_run_id: string;
  triggered_value: number;
  message: string;
  acknowledged: boolean;
  created_at: string;
}

export interface DashboardData {
  total_pipelines: number;
  active_pipelines: number;
  recent_runs: Array<{
    id: string;
    pipeline_id: string;
    environment: string;
    status: string;
    created_at: string;
  }>;
  active_alarms: number;
  success_rate_7d: number;
}

export interface SQLScript {
  id: string;
  name: string;
  description: string | null;
  dataset_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface SQLScriptVersion {
  id: string;
  script_id: string;
  major_version: number;
  minor_version: number;
  sql_body: string;
  change_description: string | null;
  env_config: Record<string, Record<string, string>>;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
}
