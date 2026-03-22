import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchPipeline, fetchSteps, fetchRuns, triggerRun } from '../api/pipelines';
import { fetchDatasets } from '../api/datasets';
import { fetchAlarmEvents, acknowledgeAlarm, fetchScripts, createScript, createScriptVersion } from '../api/monitoring';
import StatusBadge from '../components/common/StatusBadge';
import Editor from '@monaco-editor/react';
import { ArrowLeft, Play, Settings, Code2, BookOpen, Rocket, Bell, Plus, X, ChevronDown } from 'lucide-react';
import { format } from 'date-fns';
import api from '../api/client';
import type { PipelineStep } from '../types/pipeline';
import type { SQLScript, SQLScriptVersion, AlarmRule } from '../types/monitoring';

const TABS = [
  { id: 'config', label: 'Config', icon: Settings },
  { id: 'transformations', label: 'Transformations', icon: Code2 },
  { id: 'notebook', label: 'Notebook', icon: BookOpen },
  { id: 'deployments', label: 'Deployments', icon: Rocket },
  { id: 'alarms', label: 'Alarms', icon: Bell },
] as const;

type TabId = typeof TABS[number]['id'];

function ConfigTab({ pipelineId }: { pipelineId: string }) {
  const { data: pipeline } = useQuery({ queryKey: ['pipeline', pipelineId], queryFn: () => fetchPipeline(pipelineId) });
  const { data: datasets } = useQuery({ queryKey: ['datasets'], queryFn: () => fetchDatasets(1, 100) });
  const { data: steps } = useQuery({ queryKey: ['pipeline-steps', pipelineId], queryFn: () => fetchSteps(pipelineId) });

  if (!pipeline) return null;

  return (
    <div className="space-y-6">
      <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg p-5">
        <h3 className="text-[13px] font-medium text-[#6b6b7b] mb-4 uppercase tracking-wider">Pipeline Configuration</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-[12px] text-[#4a4a58] mb-1 block">Name</label>
            <div className="text-[14px] text-white">{pipeline.name}</div>
          </div>
          <div>
            <label className="text-[12px] text-[#4a4a58] mb-1 block">Dataset</label>
            <div className="text-[14px] text-white">
              {datasets?.items.find(d => d.id === pipeline.dataset_id)?.name || '—'}
            </div>
          </div>
          <div className="col-span-2">
            <label className="text-[12px] text-[#4a4a58] mb-1 block">Description</label>
            <div className="text-[13px] text-[#8a8a9b]">{pipeline.description || '—'}</div>
          </div>
        </div>
      </div>

      <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg p-5">
        <h3 className="text-[13px] font-medium text-[#6b6b7b] mb-4 uppercase tracking-wider">Steps ({steps?.length || 0})</h3>
        {steps?.map((step, i) => (
          <div key={step.id} className="flex items-center gap-3 py-2 border-b border-[#1a1a25] last:border-0">
            <span className="w-6 h-6 rounded bg-[#12121e] border border-[#1a1a25] flex items-center justify-center text-[11px] text-[#4a4a58] font-mono">{i + 1}</span>
            <span className="text-[13px] text-white flex-1">{step.step_name}</span>
            <span className="text-[11px] text-[#3a3a48] font-mono">{step.timeout_seconds}s</span>
          </div>
        ))}
        {(!steps || steps.length === 0) && <p className="text-[13px] text-[#3a3a48]">No steps configured</p>}
      </div>
    </div>
  );
}

function TransformationsTab({ pipelineId }: { pipelineId: string }) {
  const queryClient = useQueryClient();
  const { data: scripts } = useQuery({ queryKey: ['scripts'], queryFn: fetchScripts });
  const [selectedScript, setSelectedScript] = useState<string | null>(null);
  const [sqlBody, setSqlBody] = useState('-- Write your SQL transformation\nSELECT * FROM source_table;');
  const [newName, setNewName] = useState('');
  const [showNew, setShowNew] = useState(false);

  const { data: versions } = useQuery({
    queryKey: ['script-versions', selectedScript],
    queryFn: () => fetchScriptVersions(selectedScript!),
    enabled: !!selectedScript,
  });

  // Load latest version SQL when selecting a script
  const fetchScriptVersions = async (id: string): Promise<SQLScriptVersion[]> => {
    const { data } = await api.get(`/scripts/${id}/versions`);
    if (data.length > 0) setSqlBody(data[0].sql_body);
    return data;
  };

  const createMutation = useMutation({
    mutationFn: () => createScript({ name: newName }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['scripts'] });
      setSelectedScript(data.id);
      setNewName('');
      setShowNew(false);
    },
  });

  const saveMutation = useMutation({
    mutationFn: () => createScriptVersion(selectedScript!, {
      major_version: 1,
      minor_version: (versions?.length || 0),
      sql_body: sqlBody,
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['script-versions', selectedScript] }),
  });

  return (
    <div className="flex gap-4 h-[calc(100vh-200px)]">
      <div className="w-52 flex-shrink-0">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[12px] text-[#6b6b7b] uppercase tracking-wider font-medium">Scripts</span>
          <button onClick={() => setShowNew(true)} className="text-blue-400 hover:text-blue-300"><Plus size={14} /></button>
        </div>
        {showNew && (
          <div className="mb-3 p-2 bg-[#0d0d14] border border-[#1a1a25] rounded-lg">
            <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Script name" className="w-full bg-transparent border border-[#1a1a25] rounded px-2 py-1 text-[12px] text-white mb-2 placeholder-[#3a3a48]" />
            <div className="flex gap-1">
              <button onClick={() => createMutation.mutate()} className="px-2 py-1 bg-blue-600 text-white rounded text-[11px]">Create</button>
              <button onClick={() => setShowNew(false)} className="px-2 py-1 text-[#4a4a58] text-[11px]">Cancel</button>
            </div>
          </div>
        )}
        <div className="space-y-0.5">
          {scripts?.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedScript(s.id)}
              className={`w-full text-left px-2.5 py-2 rounded-md text-[13px] transition-colors ${
                selectedScript === s.id
                  ? 'bg-[#16162a] text-white'
                  : 'text-[#6b6b7b] hover:text-[#a0a0b0] hover:bg-[#0f0f1a]'
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-[#0d0d14] border border-[#1a1a25] rounded-lg overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#1a1a25]">
          <span className="text-[13px] text-[#6b6b7b]">
            {selectedScript ? scripts?.find(s => s.id === selectedScript)?.name : 'Select a script'}
          </span>
          {selectedScript && (
            <button onClick={() => saveMutation.mutate()} className="px-3 py-1 bg-blue-600 text-white rounded text-[12px] hover:bg-blue-500">Save</button>
          )}
        </div>
        <div className="flex-1">
          <Editor
            height="100%"
            language="sql"
            theme="vs-dark"
            value={sqlBody}
            onChange={(v) => setSqlBody(v || '')}
            options={{ minimap: { enabled: false }, fontSize: 13, lineNumbers: 'on', scrollBeyondLastLine: false, fontFamily: "'JetBrains Mono', monospace", padding: { top: 12 } }}
          />
        </div>
      </div>
    </div>
  );
}

function NotebookTab({ pipelineId }: { pipelineId: string }) {
  const { data: scripts } = useQuery({ queryKey: ['scripts'], queryFn: fetchScripts });
  const [cells, setCells] = useState<Array<{ id: string; sql: string; output: string | null; running: boolean }>>([
    { id: '1', sql: '-- Cell 1: Query your data\nSELECT 1 AS test;', output: null, running: false },
  ]);

  const addCell = () => {
    setCells([...cells, { id: String(Date.now()), sql: '-- New cell\n', output: null, running: false }]);
  };

  const updateCell = (id: string, sql: string) => {
    setCells(cells.map(c => c.id === id ? { ...c, sql } : c));
  };

  const runCell = async (id: string) => {
    setCells(cells.map(c => c.id === id ? { ...c, running: true, output: null } : c));
    // Simulate execution
    setTimeout(() => {
      setCells(prev => prev.map(c => c.id === id ? { ...c, running: false, output: 'Query executed successfully. 1 row returned.' } : c));
    }, 1000);
  };

  const runAll = () => cells.forEach(c => runCell(c.id));

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <span className="text-[12px] text-[#6b6b7b] uppercase tracking-wider font-medium">Notebook</span>
        <div className="flex gap-2">
          <button onClick={addCell} className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] text-[#6b6b7b] border border-[#1a1a25] rounded-lg hover:border-[#2a2a35] hover:text-white transition-colors">
            <Plus size={12} /> Cell
          </button>
          <button onClick={runAll} className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg hover:bg-emerald-500/20 transition-colors">
            <Play size={12} /> Run All
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {cells.map((cell, i) => (
          <div key={cell.id} className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-[#1a1a25]">
              <span className="text-[11px] text-[#3a3a48] font-mono">In [{i + 1}]</span>
              <div className="flex gap-2">
                <button
                  onClick={() => runCell(cell.id)}
                  className="flex items-center gap-1 px-2 py-0.5 text-[11px] text-emerald-400 hover:bg-emerald-500/10 rounded transition-colors"
                >
                  <Play size={10} /> Run
                </button>
                <button
                  onClick={() => setCells(cells.filter(c => c.id !== cell.id))}
                  className="text-[#2a2a35] hover:text-red-400 transition-colors"
                >
                  <X size={12} />
                </button>
              </div>
            </div>
            <div className="h-28">
              <Editor
                height="100%"
                language="sql"
                theme="vs-dark"
                value={cell.sql}
                onChange={(v) => updateCell(cell.id, v || '')}
                options={{ minimap: { enabled: false }, fontSize: 13, lineNumbers: 'off', scrollBeyondLastLine: false, fontFamily: "'JetBrains Mono', monospace", padding: { top: 8 }, overviewRulerLanes: 0, scrollbar: { vertical: 'hidden' } }}
              />
            </div>
            {cell.running && (
              <div className="px-3 py-2 border-t border-[#1a1a25] text-[12px] text-blue-400 font-mono">Running...</div>
            )}
            {cell.output && (
              <div className="px-3 py-2 border-t border-[#1a1a25] text-[12px] text-emerald-400 font-mono">{cell.output}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function DeploymentsTab({ pipelineId }: { pipelineId: string }) {
  const queryClient = useQueryClient();
  const { data: runs } = useQuery({ queryKey: ['pipeline-runs', pipelineId], queryFn: () => fetchRuns(pipelineId) });
  const [env, setEnv] = useState<'qa' | 'prod'>('qa');

  const triggerMutation = useMutation({
    mutationFn: () => triggerRun(pipelineId, env),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipeline-runs', pipelineId] }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <span className="text-[12px] text-[#6b6b7b] uppercase tracking-wider font-medium">Deployment History</span>
        <div className="flex items-center gap-2">
          <select value={env} onChange={(e) => setEnv(e.target.value as 'qa' | 'prod')} className="bg-[#12121e] border border-[#1a1a25] rounded-lg px-3 py-1.5 text-[13px] text-white">
            <option value="qa" className="bg-[#12121e]">QA</option>
            <option value="prod" className="bg-[#12121e]">Production</option>
          </select>
          <button
            onClick={() => {
              if (env === 'prod' && !confirm('Deploy to production?')) return;
              triggerMutation.mutate();
            }}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 text-white text-[13px] font-medium rounded-lg hover:bg-emerald-500 transition-colors"
          >
            <Rocket size={13} /> Deploy
          </button>
        </div>
      </div>

      <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#1a1a25] text-left text-[11px] text-[#4a4a58] uppercase tracking-wider">
              <th className="py-2.5 px-4 font-medium">Status</th>
              <th className="py-2.5 px-4 font-medium">Environment</th>
              <th className="py-2.5 px-4 font-medium">Triggered By</th>
              <th className="py-2.5 px-4 font-medium">Started</th>
              <th className="py-2.5 px-4 font-medium">Duration</th>
            </tr>
          </thead>
          <tbody>
            {runs?.map((run) => (
              <tr key={run.id} className="border-t border-[#1a1a25] hover:bg-[#0f0f1a]">
                <td className="py-2.5 px-4"><StatusBadge status={run.status} /></td>
                <td className="py-2.5 px-4 text-[13px] text-[#8a8a9b]">{run.environment}</td>
                <td className="py-2.5 px-4 text-[13px] text-[#6b6b7b]">{run.triggered_by || '—'}</td>
                <td className="py-2.5 px-4 text-[12px] text-[#4a4a58] font-mono">
                  {run.started_at ? format(new Date(run.started_at), 'MMM d, HH:mm') : '—'}
                </td>
                <td className="py-2.5 px-4 text-[12px] text-[#4a4a58] font-mono">
                  {run.started_at && run.completed_at
                    ? `${Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s`
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {(!runs || runs.length === 0) && (
          <div className="py-8 text-center text-[13px] text-[#3a3a48]">No deployments yet</div>
        )}
      </div>
    </div>
  );
}

function AlarmsTab({ pipelineId }: { pipelineId: string }) {
  const queryClient = useQueryClient();
  const { data: alarms } = useQuery({
    queryKey: ['pipeline-alarms', pipelineId],
    queryFn: async () => { const { data } = await api.get(`/pipelines/${pipelineId}/alarms`); return data as AlarmRule[]; },
  });
  const { data: events } = useQuery({
    queryKey: ['alarm-events', pipelineId],
    queryFn: () => fetchAlarmEvents(false),
  });

  const [showNew, setShowNew] = useState(false);
  const [name, setName] = useState('');
  const [metric, setMetric] = useState('row_count');
  const [condition, setCondition] = useState('lt');
  const [threshold, setThreshold] = useState('0');

  const createAlarm = useMutation({
    mutationFn: () => api.post(`/pipelines/${pipelineId}/alarms`, { name, metric_name: metric, condition, threshold: parseFloat(threshold) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-alarms', pipelineId] });
      setShowNew(false);
      setName('');
    },
  });

  const ackMutation = useMutation({
    mutationFn: acknowledgeAlarm,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alarm-events'] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-[12px] text-[#6b6b7b] uppercase tracking-wider font-medium">Alarm Rules</span>
          <button onClick={() => setShowNew(!showNew)} className="flex items-center gap-1.5 text-[12px] text-blue-400 hover:text-blue-300">
            <Plus size={12} /> Add Rule
          </button>
        </div>

        {showNew && (
          <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg p-4 mb-3">
            <div className="grid grid-cols-4 gap-3 mb-3">
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Alarm name" className="bg-[#12121e] border border-[#1a1a25] rounded px-2 py-1.5 text-[12px] text-white placeholder-[#3a3a48]" />
              <select value={metric} onChange={(e) => setMetric(e.target.value)} className="bg-[#12121e] border border-[#1a1a25] rounded px-2 py-1.5 text-[12px] text-white">
                <option value="row_count" className="bg-[#12121e]">Row Count</option>
                <option value="null_rate" className="bg-[#12121e]">Null Rate</option>
              </select>
              <select value={condition} onChange={(e) => setCondition(e.target.value)} className="bg-[#12121e] border border-[#1a1a25] rounded px-2 py-1.5 text-[12px] text-white">
                <option value="lt" className="bg-[#12121e]">&lt;</option>
                <option value="gt" className="bg-[#12121e]">&gt;</option>
                <option value="deviation_pct" className="bg-[#12121e]">Deviation %</option>
              </select>
              <input value={threshold} onChange={(e) => setThreshold(e.target.value)} placeholder="Threshold" type="number" className="bg-[#12121e] border border-[#1a1a25] rounded px-2 py-1.5 text-[12px] text-white placeholder-[#3a3a48]" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowNew(false)} className="text-[12px] text-[#4a4a58]">Cancel</button>
              <button onClick={() => createAlarm.mutate()} className="px-3 py-1 bg-blue-600 text-white text-[12px] rounded">Create</button>
            </div>
          </div>
        )}

        <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg overflow-hidden">
          {alarms?.map((alarm) => (
            <div key={alarm.id} className="flex items-center justify-between px-4 py-2.5 border-b border-[#1a1a25] last:border-0">
              <div>
                <span className="text-[13px] text-white">{alarm.name}</span>
                <span className="text-[11px] text-[#4a4a58] ml-3 font-mono">{alarm.metric_name} {alarm.condition} {alarm.threshold}</span>
              </div>
              <StatusBadge status={alarm.is_active ? 'success' : 'cancelled'} />
            </div>
          ))}
          {(!alarms || alarms.length === 0) && <div className="py-6 text-center text-[13px] text-[#3a3a48]">No alarm rules</div>}
        </div>
      </div>

      <div>
        <span className="text-[12px] text-[#6b6b7b] uppercase tracking-wider font-medium block mb-3">Recent Events</span>
        <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg overflow-hidden">
          {events?.map((event) => (
            <div key={event.id} className="flex items-center justify-between px-4 py-2.5 border-b border-[#1a1a25] last:border-0">
              <div>
                <p className="text-[13px] text-[#8a8a9b]">{event.message}</p>
                <span className="text-[11px] text-[#3a3a48] font-mono">{format(new Date(event.created_at), 'MMM d, HH:mm')}</span>
              </div>
              <button onClick={() => ackMutation.mutate(event.id)} className="px-2 py-1 text-[11px] text-[#6b6b7b] border border-[#1a1a25] rounded hover:border-[#2a2a35] hover:text-white transition-colors">
                Ack
              </button>
            </div>
          ))}
          {(!events || events.length === 0) && <div className="py-6 text-center text-[13px] text-emerald-500/60">No active alerts</div>}
        </div>
      </div>
    </div>
  );
}

export default function PipelineDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<TabId>('config');
  const { data: pipeline } = useQuery({ queryKey: ['pipeline', id], queryFn: () => fetchPipeline(id!) });

  if (!pipeline) return <div className="text-[#4a4a58] text-sm">Loading...</div>;

  return (
    <div>
      <Link to="/pipelines" className="inline-flex items-center gap-1.5 text-[12px] text-[#4a4a58] hover:text-[#8a8a9b] transition-colors mb-5">
        <ArrowLeft size={12} /> Pipelines
      </Link>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-white">{pipeline.name}</h1>
          {pipeline.description && <p className="text-[13px] text-[#5a5a6b] mt-1">{pipeline.description}</p>}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-[#1a1a25]">
        {TABS.map(({ id: tabId, label, icon: Icon }) => (
          <button
            key={tabId}
            onClick={() => setActiveTab(tabId)}
            className={`flex items-center gap-2 px-4 py-2.5 text-[13px] border-b-2 transition-colors -mb-px ${
              activeTab === tabId
                ? 'border-blue-500 text-white'
                : 'border-transparent text-[#5a5a6b] hover:text-[#8a8a9b]'
            }`}
          >
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'config' && <ConfigTab pipelineId={id!} />}
      {activeTab === 'transformations' && <TransformationsTab pipelineId={id!} />}
      {activeTab === 'notebook' && <NotebookTab pipelineId={id!} />}
      {activeTab === 'deployments' && <DeploymentsTab pipelineId={id!} />}
      {activeTab === 'alarms' && <AlarmsTab pipelineId={id!} />}
    </div>
  );
}
