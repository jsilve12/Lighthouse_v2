import api from './client';
import type { Folder } from '../types/folder';

export const fetchFolders = async (datasetId: string): Promise<Folder[]> => {
  const { data } = await api.get(`/datasets/${datasetId}/folders`);
  return data;
};

export const fetchFolder = async (folderId: string): Promise<Folder> => {
  const { data } = await api.get(`/folders/${folderId}`);
  return data;
};

export const createFolder = async (datasetId: string, body: Partial<Folder>): Promise<Folder> => {
  const { data } = await api.post(`/datasets/${datasetId}/folders`, body);
  return data;
};
