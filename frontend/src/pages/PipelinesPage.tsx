import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchPipelines } from '../api/pipelines';
import { GitBranch, ChevronRight } from 'lucide-react';

export default function PipelinesPage() {
  const { data: pipelines, isLoading } = useQuery({ queryKey: ['pipelines'], queryFn: fetchPipelines });

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Pipelines</h1>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="grid gap-3">
          {pipelines?.map((pipeline) => (
            <Link
              key={pipeline.id}
              to={`/pipelines/${pipeline.id}`}
              className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4 hover:border-blue-300 transition-colors"
            >
              <div className="flex items-center gap-3">
                <GitBranch className="text-green-500" size={18} />
                <div>
                  <h3 className="font-medium text-gray-900">{pipeline.name}</h3>
                  {pipeline.description && <p className="text-xs text-gray-500">{pipeline.description}</p>}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${pipeline.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  {pipeline.is_active ? 'Active' : 'Inactive'}
                </span>
                <span className="text-sm text-gray-400">{pipeline.step_count} steps</span>
                <ChevronRight size={16} className="text-gray-400" />
              </div>
            </Link>
          ))}
          {pipelines?.length === 0 && <p className="text-gray-400 text-sm">No pipelines configured</p>}
        </div>
      )}
    </div>
  );
}
