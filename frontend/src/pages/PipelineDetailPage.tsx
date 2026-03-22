import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchPipeline, fetchSteps, fetchRuns, triggerRun } from '../api/pipelines';
import StatusBadge from '../components/common/StatusBadge';
import { ArrowLeft, Play } from 'lucide-react';
import { format } from 'date-fns';

export default function PipelineDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [triggerEnv, setTriggerEnv] = useState<'qa' | 'prod'>('qa');

  const { data: pipeline } = useQuery({ queryKey: ['pipeline', id], queryFn: () => fetchPipeline(id!) });
  const { data: steps } = useQuery({ queryKey: ['pipeline-steps', id], queryFn: () => fetchSteps(id!) });
  const { data: runs } = useQuery({ queryKey: ['pipeline-runs', id], queryFn: () => fetchRuns(id!) });

  const triggerMutation = useMutation({
    mutationFn: () => triggerRun(id!, triggerEnv),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipeline-runs', id] }),
  });

  if (!pipeline) return <div className="text-gray-500">Loading...</div>;

  return (
    <div>
      <Link to="/pipelines" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={14} /> Back to Pipelines
      </Link>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{pipeline.name}</h1>
        <div className="flex items-center gap-2">
          <select
            value={triggerEnv}
            onChange={(e) => setTriggerEnv(e.target.value as 'qa' | 'prod')}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="qa">QA</option>
            <option value="prod">Production</option>
          </select>
          <button
            onClick={() => {
              if (triggerEnv === 'prod' && !window.confirm('Trigger production run?')) return;
              triggerMutation.mutate();
            }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
          >
            <Play size={14} /> Run
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Steps ({steps?.length || 0})</h2>
          <div className="bg-white rounded-lg border border-gray-200">
            {steps?.map((step, i) => (
              <div key={step.id} className="flex items-center justify-between p-3 border-b last:border-b-0">
                <div className="flex items-center gap-3">
                  <span className="text-xs bg-gray-100 text-gray-500 rounded-full w-6 h-6 flex items-center justify-center">
                    {i + 1}
                  </span>
                  <span className="text-sm font-medium text-gray-700">{step.step_name}</span>
                </div>
                <span className="text-xs text-gray-400">{step.timeout_seconds}s timeout</span>
              </div>
            ))}
            {(!steps || steps.length === 0) && (
              <p className="p-4 text-sm text-gray-400">No steps configured</p>
            )}
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Runs</h2>
          <div className="bg-white rounded-lg border border-gray-200">
            {runs?.map((run) => (
              <Link
                key={run.id}
                to={`/pipelines/${id}/runs/${run.id}`}
                className="flex items-center justify-between p-3 border-b last:border-b-0 hover:bg-gray-50"
              >
                <div className="flex items-center gap-3">
                  <StatusBadge status={run.status} />
                  <span className="text-xs text-gray-500">{run.environment}</span>
                </div>
                <div className="text-right text-xs text-gray-400">
                  <div>{run.triggered_by}</div>
                  <div>{run.created_at ? format(new Date(run.created_at), 'MMM d, HH:mm') : '-'}</div>
                </div>
              </Link>
            ))}
            {(!runs || runs.length === 0) && (
              <p className="p-4 text-sm text-gray-400">No runs yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
