export interface SchemaField {
  id: string;
  schema_version_id: string;
  name: string;
  field_type: string;
  nullable: boolean;
  description: string | null;
  is_encrypted: boolean;
  is_pii: boolean;
  is_financial: boolean;
  parent_field_id: string | null;
  array_element: boolean;
  sort_order: number;
  custom_metadata: Record<string, unknown>;
  children: SchemaField[];
}

export interface SchemaVersion {
  id: string;
  folder_id: string;
  major_version: number;
  minor_version: number;
  description: string | null;
  is_active: boolean;
  custom_metadata_schema: Record<string, unknown> | null;
  data_location_pattern: string | null;
  field_count: number;
  created_at: string;
  updated_at: string;
  fields?: SchemaField[];
}
