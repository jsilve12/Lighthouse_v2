export interface Folder {
  id: string;
  dataset_id: string;
  name: string;
  description: string | null;
  sort_order: number;
  schema_count: number;
  created_at: string;
  updated_at: string;
}
