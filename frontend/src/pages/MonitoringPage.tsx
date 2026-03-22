import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchDashboard, fetchAlarmEvents, acknowledgeAlarm } from '../api/monitoring';
import StatusBadge from '../components/common/StatusBadge';
import { Activity, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { format } from 'date-fns';

export default function MonitoringPage() {
  const queryClient = useQueryClient();
  const { data: dashboard } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard, refetchInterval: 30000 });
  const { data: alarmEvents } = useQuery({
    queryKey: ['alarm-events'],
    queryFn: () => fetchAlarmEvents(false),
    refetchInterval: 30000,
  });

  const ackMutation = useMutation({
    mutationFn: acknowledgeAlarm,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alarm-events'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Monitoring</h1>

      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
            <Activity size={16} /> Pipelines
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {dashboard?.active_pipelines || 0}
            <span className="text-sm text-gray-400 font-normal ml-1">/ {dashboard?.total_pipelines || 0}</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
            <CheckCircle size={16} /> Success Rate (7d)
          </div>
          <div className="text-2xl font-bold text-green-600">
            {dashboard?.success_rate_7d?.toFixed(1) || 0}%
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
            <AlertTriangle size={16} /> Active Alarms
          </div>
          <div className={`text-2xl font-bold ${(dashboard?.active_alarms || 0) > 0 ? 'text-red-600' : 'text-gray-900'}`}>
            {dashboard?.active_alarms || 0}
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
            <Clock size={16} /> Recent Runs
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {dashboard?.recent_runs?.length || 0}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Pipeline Runs</h2>
          <div className="bg-white rounded-lg border border-gray-200">
            {dashboard?.recent_runs?.map((run) => (
              <div key={run.id} className="flex items-center justify-between p-3 border-b last:border-b-0">
                <div className="flex items-center gap-3">
                  <StatusBadge status={run.status} />
                  <span className="text-xs text-gray-500">{run.environment}</span>
                </div>
                <span className="text-xs text-gray-400">
                  {run.created_at ? format(new Date(run.created_at), 'MMM d, HH:mm') : '-'}
                </span>
              </div>
            ))}
            {(!dashboard?.recent_runs || dashboard.recent_runs.length === 0) && (
              <p className="p-4 text-sm text-gray-400">No recent runs</p>
            )}
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Unacknowledged Alarms</h2>
          <div className="bg-white rounded-lg border border-gray-200">
            {alarmEvents?.map((event) => (
              <div key={event.id} className="flex items-center justify-between p-3 border-b last:border-b-0">
                <div>
                  <p className="text-sm text-gray-700">{event.message}</p>
                  <span className="text-xs text-gray-400">
                    {event.created_at ? format(new Date(event.created_at), 'MMM d, HH:mm') : '-'}
                  </span>
                </div>
                <button
                  onClick={() => ackMutation.mutate(event.id)}
                  className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200"
                >
                  Acknowledge
                </button>
              </div>
            ))}
            {(!alarmEvents || alarmEvents.length === 0) && (
              <p className="p-4 text-sm text-green-600">No active alarms</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
