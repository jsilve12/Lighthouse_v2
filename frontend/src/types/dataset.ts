export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  source_type: string;
  source_config: Record<string, unknown>;
  current_major_version: number;
  current_minor_version: number;
  tags: string[];
  is_financial: boolean;
  is_pii: boolean;
  folder_count: number;
  created_at: string;
  updated_at: string;
}

export interface DatasetListResponse {
  items: Dataset[];
  total: number;
  page: number;
  size: number;
}

export interface DatasetCreate {
  name: string;
  description?: string;
  source_type: string;
  source_config?: Record<string, unknown>;
  tags?: string[];
  is_financial?: boolean;
  is_pii?: boolean;
}
