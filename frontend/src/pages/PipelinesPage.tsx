import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchPipelines, createPipeline } from '../api/pipelines';
import { fetchDatasets } from '../api/datasets';
import StatusBadge from '../components/common/StatusBadge';
import { GitBranch, Plus, ChevronRight, X } from 'lucide-react';
import api from '../api/client';

function CreatePipelineModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [datasetId, setDatasetId] = useState('');
  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: () => fetchDatasets(1, 100) });

  const createMutation = useMutation({
    mutationFn: () => createPipeline({ name, description: description || undefined, dataset_id: datasetId || undefined } as never),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-[#12121e] border border-[#1a1a25] rounded-xl p-6 w-[440px] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-[15px] font-semibold text-white">New Pipeline</h3>
          <button onClick={onClose} className="text-[#4a4a58] hover:text-white"><X size={16} /></button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-[12px] text-[#6b6b7b] mb-1.5 block">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my-pipeline"
              className="w-full bg-[#0d0d14] border border-[#1a1a25] rounded-lg px-3 py-2 text-[13px] text-white placeholder-[#3a3a48] focus:border-blue-500/50"
            />
          </div>
          <div>
            <label className="text-[12px] text-[#6b6b7b] mb-1.5 block">Dataset</label>
            <select
              value={datasetId}
              onChange={(e) => setDatasetId(e.target.value)}
              className="w-full bg-[#0d0d14] border border-[#1a1a25] rounded-lg px-3 py-2 text-[13px] text-white"
            >
              <option value="" className="bg-[#12121e]">None</option>
              {datasets?.items.map((d) => (
                <option key={d.id} value={d.id} className="bg-[#12121e]">{d.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[12px] text-[#6b6b7b] mb-1.5 block">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description..."
              className="w-full bg-[#0d0d14] border border-[#1a1a25] rounded-lg px-3 py-2 text-[13px] text-white placeholder-[#3a3a48] resize-none h-16 focus:border-blue-500/50"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button onClick={onClose} className="px-4 py-2 text-[13px] text-[#6b6b7b] hover:text-white">Cancel</button>
            <button
              onClick={() => createMutation.mutate()}
              disabled={!name}
              className="px-4 py-2 bg-blue-600 text-white text-[13px] font-medium rounded-lg hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Create
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PipelinesPage() {
  const [showCreate, setShowCreate] = useState(false);
  const queryClient = useQueryClient();
  const { data: pipelines, isLoading } = useQuery({ queryKey: ['pipelines'], queryFn: fetchPipelines });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/pipelines/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipelines'] }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold text-white">Pipelines</h1>
          <p className="text-[13px] text-[#6b6b7b] mt-1">Transformation workflows and deployments</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-[13px] font-medium rounded-lg hover:bg-blue-500 transition-colors"
        >
          <Plus size={14} /> New Pipeline
        </button>
      </div>

      {isLoading ? (
        <div className="text-[#4a4a58] text-sm">Loading...</div>
      ) : (
        <div className="space-y-2">
          {pipelines?.map((pipeline) => (
            <div
              key={pipeline.id}
              className="group flex items-center justify-between bg-[#0d0d14] border border-[#1a1a25] rounded-lg px-5 py-4 hover:border-[#2a2a3a] transition-all"
            >
              <Link to={`/pipelines/${pipeline.id}`} className="flex items-center gap-4 flex-1">
                <div className={`w-8 h-8 rounded-md flex items-center justify-center border ${
                  pipeline.is_active
                    ? 'bg-emerald-500/10 border-emerald-500/20'
                    : 'bg-[#12121e] border-[#1a1a25]'
                }`}>
                  <GitBranch size={14} className={pipeline.is_active ? 'text-emerald-400' : 'text-[#4a4a58]'} />
                </div>
                <div>
                  <h3 className="text-[14px] font-medium text-white">{pipeline.name}</h3>
                  {pipeline.description && (
                    <p className="text-[12px] text-[#5a5a6b] mt-0.5">{pipeline.description}</p>
                  )}
                </div>
              </Link>
              <div className="flex items-center gap-3">
                <span className="text-[11px] text-[#4a4a58]">{pipeline.step_count} steps</span>
                <StatusBadge status={pipeline.is_active ? 'success' : 'cancelled'} />
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    if (confirm(`Delete pipeline "${pipeline.name}"?`)) {
                      deleteMutation.mutate(pipeline.id);
                    }
                  }}
                  className="text-[#2a2a35] hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                >
                  <X size={14} />
                </button>
                <Link to={`/pipelines/${pipeline.id}`}>
                  <ChevronRight size={14} className="text-[#2a2a35] group-hover:text-[#4a4a58]" />
                </Link>
              </div>
            </div>
          ))}
          {pipelines?.length === 0 && (
            <div className="text-center py-12 text-[#3a3a48] text-[13px]">
              No pipelines yet. Create one to get started.
            </div>
          )}
        </div>
      )}

      {showCreate && <CreatePipelineModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}
