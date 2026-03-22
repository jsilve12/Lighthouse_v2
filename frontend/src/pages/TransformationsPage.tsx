import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchScripts, fetchScriptVersions, createScript, createScriptVersion } from '../api/monitoring';
import Editor from '@monaco-editor/react';
import { Plus } from 'lucide-react';

export default function TransformationsPage() {
  const queryClient = useQueryClient();
  const [selectedScript, setSelectedScript] = useState<string | null>(null);
  const [sqlBody, setSqlBody] = useState('-- Write your SQL here\nSELECT 1;');
  const [newScriptName, setNewScriptName] = useState('');
  const [showNewForm, setShowNewForm] = useState(false);

  const { data: scripts } = useQuery({ queryKey: ['scripts'], queryFn: fetchScripts });
  const { data: versions } = useQuery({
    queryKey: ['script-versions', selectedScript],
    queryFn: () => fetchScriptVersions(selectedScript!),
    enabled: !!selectedScript,
  });

  const createScriptMutation = useMutation({
    mutationFn: () => createScript({ name: newScriptName }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scripts'] });
      setNewScriptName('');
      setShowNewForm(false);
    },
  });

  const saveVersionMutation = useMutation({
    mutationFn: () =>
      createScriptVersion(selectedScript!, {
        major_version: 1,
        minor_version: (versions?.length || 0),
        sql_body: sqlBody,
        change_description: 'Updated via editor',
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['script-versions', selectedScript] }),
  });

  return (
    <div className="flex gap-6 h-[calc(100vh-48px)]">
      <div className="w-64 flex-shrink-0">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">SQL Scripts</h2>
          <button onClick={() => setShowNewForm(true)} className="text-blue-600 hover:text-blue-700">
            <Plus size={18} />
          </button>
        </div>

        {showNewForm && (
          <div className="mb-3 p-2 bg-white rounded border">
            <input
              type="text"
              value={newScriptName}
              onChange={(e) => setNewScriptName(e.target.value)}
              placeholder="Script name"
              className="w-full px-2 py-1 border rounded text-sm mb-2"
            />
            <div className="flex gap-1">
              <button
                onClick={() => createScriptMutation.mutate()}
                className="px-2 py-1 bg-blue-600 text-white rounded text-xs"
              >
                Create
              </button>
              <button onClick={() => setShowNewForm(false)} className="px-2 py-1 text-gray-500 text-xs">
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="space-y-1">
          {scripts?.map((script) => (
            <button
              key={script.id}
              onClick={() => {
                setSelectedScript(script.id);
              }}
              className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                selectedScript === script.id
                  ? 'bg-blue-100 text-blue-800'
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
            >
              {script.name}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b bg-gray-50">
          <span className="text-sm font-medium text-gray-700">
            {selectedScript ? scripts?.find((s) => s.id === selectedScript)?.name : 'Select a script'}
          </span>
          {selectedScript && (
            <button
              onClick={() => saveVersionMutation.mutate()}
              className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Save Version
            </button>
          )}
        </div>
        <div className="flex-1">
          <Editor
            height="100%"
            language="sql"
            theme="vs-dark"
            value={sqlBody}
            onChange={(value) => setSqlBody(value || '')}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
            }}
          />
        </div>
      </div>
    </div>
  );
}
