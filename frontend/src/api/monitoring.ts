import api from './client';
import type { DashboardData, AlarmEvent, SQLScript, SQLScriptVersion } from '../types/monitoring';

export const fetchDashboard = async (): Promise<DashboardData> => {
  const { data } = await api.get('/monitoring/dashboard');
  return data;
};

export const fetchAlarmEvents = async (acknowledged?: boolean): Promise<AlarmEvent[]> => {
  const params: Record<string, string> = {};
  if (acknowledged !== undefined) params.acknowledged = String(acknowledged);
  const { data } = await api.get('/alarm-events', { params });
  return data;
};

export const acknowledgeAlarm = async (eventId: string): Promise<void> => {
  await api.post(`/alarm-events/${eventId}/acknowledge`);
};

export const fetchScripts = async (): Promise<SQLScript[]> => {
  const { data } = await api.get('/scripts');
  return data;
};

export const fetchScriptVersions = async (scriptId: string): Promise<SQLScriptVersion[]> => {
  const { data } = await api.get(`/scripts/${scriptId}/versions`);
  return data;
};

export const createScript = async (body: Partial<SQLScript>): Promise<SQLScript> => {
  const { data } = await api.post('/scripts', body);
  return data;
};

export const createScriptVersion = async (scriptId: string, body: Partial<SQLScriptVersion>): Promise<SQLScriptVersion> => {
  const { data } = await api.post(`/scripts/${scriptId}/versions`, body);
  return data;
};

export const fetchMe = async () => {
  const { data } = await api.get('/auth/me');
  return data;
};
