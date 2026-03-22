import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchDashboard, fetchAlarmEvents, acknowledgeAlarm } from '../api/monitoring';
import StatusBadge from '../components/common/StatusBadge';
import { Activity, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { format } from 'date-fns';

function StatCard({ icon: Icon, label, value, accent }: { icon: typeof Activity; label: string; value: string | number; accent?: string }) {
  return (
    <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg p-4">
      <div className="flex items-center gap-2 text-[12px] text-[#4a4a58] mb-2">
        <Icon size={13} /> {label}
      </div>
      <div className={`text-2xl font-semibold tracking-tight ${accent || 'text-white'}`}>{value}</div>
    </div>
  );
}

export default function MonitoringPage() {
  const queryClient = useQueryClient();
  const { data: dashboard } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard, refetchInterval: 30000 });
  const { data: alarmEvents } = useQuery({ queryKey: ['alarm-events'], queryFn: () => fetchAlarmEvents(false), refetchInterval: 30000 });

  const ackMutation = useMutation({
    mutationFn: acknowledgeAlarm,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alarm-events'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-xl font-semibold text-white">Monitoring</h1>
        <p className="text-[13px] text-[#6b6b7b] mt-1">Pipeline health and alerts</p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-8">
        <StatCard icon={Activity} label="Active Pipelines" value={`${dashboard?.active_pipelines || 0} / ${dashboard?.total_pipelines || 0}`} />
        <StatCard icon={CheckCircle} label="Success Rate (7d)" value={`${dashboard?.success_rate_7d?.toFixed(1) || 0}%`} accent="text-emerald-400" />
        <StatCard icon={AlertTriangle} label="Active Alarms" value={dashboard?.active_alarms || 0} accent={(dashboard?.active_alarms || 0) > 0 ? 'text-red-400' : 'text-white'} />
        <StatCard icon={Clock} label="Recent Runs" value={dashboard?.recent_runs?.length || 0} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="text-[12px] text-[#6b6b7b] uppercase tracking-wider font-medium mb-3">Recent Runs</h2>
          <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg overflow-hidden">
            {dashboard?.recent_runs?.map((run) => (
              <div key={run.id} className="flex items-center justify-between px-4 py-2.5 border-b border-[#1a1a25] last:border-0">
                <div className="flex items-center gap-3">
                  <StatusBadge status={run.status} />
                  <span className="text-[12px] text-[#6b6b7b]">{run.environment}</span>
                </div>
                <span className="text-[11px] text-[#3a3a48] font-mono">
                  {run.created_at ? format(new Date(run.created_at), 'MMM d, HH:mm') : '—'}
                </span>
              </div>
            ))}
            {(!dashboard?.recent_runs || dashboard.recent_runs.length === 0) && (
              <div className="py-8 text-center text-[13px] text-[#3a3a48]">No recent runs</div>
            )}
          </div>
        </div>

        <div>
          <h2 className="text-[12px] text-[#6b6b7b] uppercase tracking-wider font-medium mb-3">Unacknowledged Alarms</h2>
          <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg overflow-hidden">
            {alarmEvents?.map((event) => (
              <div key={event.id} className="flex items-center justify-between px-4 py-2.5 border-b border-[#1a1a25] last:border-0">
                <div>
                  <p className="text-[13px] text-[#8a8a9b]">{event.message}</p>
                  <span className="text-[11px] text-[#3a3a48] font-mono">
                    {format(new Date(event.created_at), 'MMM d, HH:mm')}
                  </span>
                </div>
                <button
                  onClick={() => ackMutation.mutate(event.id)}
                  className="px-2 py-1 text-[11px] text-[#6b6b7b] border border-[#1a1a25] rounded hover:border-[#2a2a35] hover:text-white transition-colors"
                >
                  Ack
                </button>
              </div>
            ))}
            {(!alarmEvents || alarmEvents.length === 0) && (
              <div className="py-8 text-center text-[13px] text-emerald-500/60">No active alerts</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
