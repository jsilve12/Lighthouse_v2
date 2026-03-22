import api from './client';
import type { Pipeline, PipelineRun, PipelineStep } from '../types/pipeline';

export const fetchPipelines = async (): Promise<Pipeline[]> => {
  const { data } = await api.get('/pipelines');
  return data;
};

export const fetchPipeline = async (id: string): Promise<Pipeline> => {
  const { data } = await api.get(`/pipelines/${id}`);
  return data;
};

export const createPipeline = async (body: Partial<Pipeline>): Promise<Pipeline> => {
  const { data } = await api.post('/pipelines', body);
  return data;
};

export const fetchSteps = async (pipelineId: string): Promise<PipelineStep[]> => {
  const { data } = await api.get(`/pipelines/${pipelineId}/steps`);
  return data;
};

export const triggerRun = async (pipelineId: string, environment: string): Promise<PipelineRun> => {
  const { data } = await api.post(`/pipelines/${pipelineId}/trigger`, { environment });
  return data;
};

export const fetchRuns = async (pipelineId: string, page = 1): Promise<PipelineRun[]> => {
  const { data } = await api.get(`/pipelines/${pipelineId}/runs`, { params: { page } });
  return data;
};

export const fetchRun = async (runId: string) => {
  const { data } = await api.get(`/pipelines/runs/${runId}`);
  return data;
};
