import api from './client';
import type { SchemaVersion } from '../types/schema';

export const fetchSchemas = async (folderId: string): Promise<SchemaVersion[]> => {
  const { data } = await api.get(`/folders/${folderId}/schemas`);
  return data;
};

export const fetchSchema = async (schemaId: string): Promise<SchemaVersion> => {
  const { data } = await api.get(`/schemas/${schemaId}`);
  return data;
};

export const compareSchemas = async (leftId: string, rightId: string) => {
  const { data } = await api.get('/schemas/compare', { params: { left: leftId, right: rightId } });
  return data;
};
