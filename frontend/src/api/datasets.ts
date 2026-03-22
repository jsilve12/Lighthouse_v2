import api from './client';
import type { Dataset, DatasetListResponse } from '../types/dataset';

export const fetchDatasets = async (page = 1, size = 20, search?: string): Promise<DatasetListResponse> => {
  const params: Record<string, string | number> = { page, size };
  if (search) params.search = search;
  const { data } = await api.get('/datasets', { params });
  return data;
};

export const fetchDataset = async (id: string): Promise<Dataset> => {
  const { data } = await api.get(`/datasets/${id}`);
  return data;
};

export const createDataset = async (body: Partial<Dataset>): Promise<Dataset> => {
  const { data } = await api.post('/datasets', body);
  return data;
};

export const updateDataset = async (id: string, body: Partial<Dataset>): Promise<Dataset> => {
  const { data } = await api.put(`/datasets/${id}`, body);
  return data;
};

export const deleteDataset = async (id: string): Promise<void> => {
  await api.delete(`/datasets/${id}`);
};

export const bumpVersion = async (id: string, bumpType: 'major' | 'minor'): Promise<Dataset> => {
  const { data } = await api.post(`/datasets/${id}/bump-version`, { bump_type: bumpType });
  return data;
};
