import { useState, useEffect, useCallback } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchDataset } from '../api/datasets';
import { fetchFolders } from '../api/folders';
import { fetchSchemas, fetchSchema } from '../api/schemas';
import { SecurityBadge } from '../components/common/StatusBadge';
import { ArrowLeft, ChevronDown, Save } from 'lucide-react';
import api from '../api/client';
import type { SchemaField } from '../types/schema';

interface EditableField {
  id: string;
  name: string;
  field_type: string;
  nullable: boolean;
  description: string;
  is_pii: boolean;
  is_financial: boolean;
  is_encrypted: boolean;
  children: EditableField[];
}

function toEditable(fields: SchemaField[]): EditableField[] {
  return fields.map((f) => ({
    id: f.id,
    name: f.name,
    field_type: f.field_type,
    nullable: f.nullable,
    description: f.description || '',
    is_pii: f.is_pii,
    is_financial: f.is_financial,
    is_encrypted: f.is_encrypted,
    children: f.children ? toEditable(f.children) : [],
  }));
}

function fieldsChanged(original: SchemaField[], edited: EditableField[]): boolean {
  return JSON.stringify(toEditable(original)) !== JSON.stringify(edited);
}

function VersionBumpModal({
  onSave,
  onCancel,
}: {
  onSave: (bump: 'minor' | 'major', desc: string) => void;
  onCancel: () => void;
}) {
  const [bump, setBump] = useState<'minor' | 'major'>('minor');
  const [desc, setDesc] = useState('');

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={onCancel}>
      <div className="bg-[#12121e] border border-[#1a1a25] rounded-xl p-6 w-[420px] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-[15px] font-semibold text-white mb-4">Create New Version</h3>
        <div className="space-y-4">
          <div>
            <label className="text-[12px] text-[#6b6b7b] mb-2 block">Version Type</label>
            <div className="flex gap-2">
              <button
                onClick={() => setBump('minor')}
                className={`flex-1 py-2 rounded-lg text-[13px] font-medium border transition-colors ${
                  bump === 'minor'
                    ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                    : 'bg-[#0d0d14] border-[#1a1a25] text-[#6b6b7b] hover:border-[#2a2a35]'
                }`}
              >
                Minor
              </button>
              <button
                onClick={() => setBump('major')}
                className={`flex-1 py-2 rounded-lg text-[13px] font-medium border transition-colors ${
                  bump === 'major'
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                    : 'bg-[#0d0d14] border-[#1a1a25] text-[#6b6b7b] hover:border-[#2a2a35]'
                }`}
              >
                Major
              </button>
            </div>
          </div>
          <div>
            <label className="text-[12px] text-[#6b6b7b] mb-2 block">Change Description</label>
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              placeholder="Describe what changed..."
              className="w-full bg-[#0d0d14] border border-[#1a1a25] rounded-lg px-3 py-2 text-[13px] text-white placeholder-[#3a3a48] resize-none h-20 focus:border-blue-500/50"
            />
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button onClick={onCancel} className="px-4 py-2 text-[13px] text-[#6b6b7b] hover:text-white transition-colors">
              Cancel
            </button>
            <button
              onClick={() => onSave(bump, desc)}
              className="px-4 py-2 bg-blue-600 text-white text-[13px] font-medium rounded-lg hover:bg-blue-500 transition-colors"
            >
              Save Version
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function FieldToggle({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`px-1.5 py-0.5 rounded border text-[10px] font-medium tracking-wide transition-colors ${
        active ? 'opacity-100' : 'opacity-25 hover:opacity-50'
      }`}
    >
      {children}
    </button>
  );
}

function EditableFieldRow({
  field,
  depth = 0,
  onChange,
}: {
  field: EditableField;
  depth?: number;
  onChange: (updated: EditableField) => void;
}) {
  const update = (key: keyof EditableField, value: unknown) => {
    onChange({ ...field, [key]: value });
  };

  const updateChild = (index: number, child: EditableField) => {
    const newChildren = [...field.children];
    newChildren[index] = child;
    onChange({ ...field, children: newChildren });
  };

  return (
    <>
      <tr className="border-t border-[#1a1a25] hover:bg-[#0f0f1a] transition-colors">
        <td className="py-2 px-3" style={{ paddingLeft: `${depth * 20 + 12}px` }}>
          <input
            type="text"
            value={field.name}
            onChange={(e) => update('name', e.target.value)}
            className="bg-transparent text-[13px] font-mono text-white border-0 outline-none w-full"
          />
        </td>
        <td className="py-2 px-3">
          <select
            value={field.field_type}
            onChange={(e) => update('field_type', e.target.value)}
            className="bg-transparent text-[13px] text-[#8a8a9b] border-0 outline-none cursor-pointer"
          >
            {['string', 'integer', 'float', 'boolean', 'timestamp', 'date', 'object', 'array'].map((t) => (
              <option key={t} value={t} className="bg-[#12121e]">{t}</option>
            ))}
          </select>
        </td>
        <td className="py-2 px-3 text-center">
          <input
            type="checkbox"
            checked={field.nullable}
            onChange={(e) => update('nullable', e.target.checked)}
            className="accent-blue-500"
          />
        </td>
        <td className="py-2 px-3">
          <input
            type="text"
            value={field.description}
            onChange={(e) => update('description', e.target.value)}
            placeholder="—"
            className="bg-transparent text-[12px] text-[#6b6b7b] border-0 outline-none w-full placeholder-[#2a2a35]"
          />
        </td>
        <td className="py-2 px-3">
          <div className="flex gap-1">
            <FieldToggle active={field.is_pii} onClick={() => update('is_pii', !field.is_pii)}>
              <span className="text-red-400">PII</span>
            </FieldToggle>
            <FieldToggle active={field.is_financial} onClick={() => update('is_financial', !field.is_financial)}>
              <span className="text-amber-400">FIN</span>
            </FieldToggle>
            <FieldToggle active={field.is_encrypted} onClick={() => update('is_encrypted', !field.is_encrypted)}>
              <span className="text-blue-400">ENC</span>
            </FieldToggle>
          </div>
        </td>
      </tr>
      {field.children?.map((child, i) => (
        <EditableFieldRow key={child.id} field={child} depth={depth + 1} onChange={(c) => updateChild(i, c)} />
      ))}
    </>
  );
}

export default function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { data: dataset } = useQuery({ queryKey: ['dataset', id], queryFn: () => fetchDataset(id!) });
  const { data: folders } = useQuery({ queryKey: ['folders', id], queryFn: () => fetchFolders(id!) });

  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [selectedSchemaId, setSelectedSchemaId] = useState<string | null>(null);
  const [editableFields, setEditableFields] = useState<EditableField[]>([]);
  const [showBumpModal, setShowBumpModal] = useState(false);

  // Auto-select first folder
  useEffect(() => {
    if (folders?.length && !selectedFolderId) {
      setSelectedFolderId(folders[0].id);
    }
  }, [folders, selectedFolderId]);

  // Fetch schemas for selected folder
  const { data: schemas } = useQuery({
    queryKey: ['schemas', selectedFolderId],
    queryFn: () => fetchSchemas(selectedFolderId!),
    enabled: !!selectedFolderId,
  });

  // Auto-select first schema
  useEffect(() => {
    if (schemas?.length && !selectedSchemaId) {
      setSelectedSchemaId(schemas[0].id);
    }
  }, [schemas, selectedSchemaId]);

  // Fetch schema detail
  const { data: schemaDetail } = useQuery({
    queryKey: ['schema', selectedSchemaId],
    queryFn: () => fetchSchema(selectedSchemaId!),
    enabled: !!selectedSchemaId,
  });

  // Populate editable fields
  useEffect(() => {
    if (schemaDetail?.fields) {
      setEditableFields(toEditable(schemaDetail.fields));
    }
  }, [schemaDetail]);

  const hasChanges = schemaDetail?.fields ? fieldsChanged(schemaDetail.fields, editableFields) : false;

  const updateField = useCallback((index: number, field: EditableField) => {
    setEditableFields((prev) => {
      const next = [...prev];
      next[index] = field;
      return next;
    });
  }, []);

  const handleSaveVersion = async (bump: 'minor' | 'major', description: string) => {
    if (!schemaDetail || !selectedFolderId) return;
    const newMajor = bump === 'major' ? schemaDetail.major_version + 1 : schemaDetail.major_version;
    const newMinor = bump === 'major' ? 0 : schemaDetail.minor_version + 1;

    // Flatten editable fields back to creation format
    const flattenFields = (fields: EditableField[]): Array<Record<string, unknown>> =>
      fields.flatMap((f, i) => [
        {
          name: f.name,
          field_type: f.field_type,
          nullable: f.nullable,
          description: f.description || null,
          is_pii: f.is_pii,
          is_financial: f.is_financial,
          is_encrypted: f.is_encrypted,
          sort_order: i,
        },
        ...flattenFields(f.children),
      ]);

    await api.post(`/folders/${selectedFolderId}/schemas`, {
      major_version: newMajor,
      minor_version: newMinor,
      description,
      data_location_pattern: schemaDetail.data_location_pattern,
      fields: flattenFields(editableFields),
    });

    setShowBumpModal(false);
    queryClient.invalidateQueries({ queryKey: ['schemas', selectedFolderId] });
    queryClient.invalidateQueries({ queryKey: ['schema'] });
  };

  if (!dataset) return <div className="text-[#4a4a58] text-sm">Loading...</div>;

  const selectedSchema = schemas?.find((s) => s.id === selectedSchemaId);

  return (
    <div>
      <Link to="/datasets" className="inline-flex items-center gap-1.5 text-[12px] text-[#4a4a58] hover:text-[#8a8a9b] transition-colors mb-5">
        <ArrowLeft size={12} /> Datasets
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-white">{dataset.name}</h1>
            <span className="text-[10px] font-mono text-[#4a4a58] bg-[#12121e] border border-[#1a1a25] px-1.5 py-0.5 rounded">
              v{dataset.current_major_version}.{dataset.current_minor_version}
            </span>
            {dataset.is_pii && <SecurityBadge type="pii" />}
            {dataset.is_financial && <SecurityBadge type="financial" />}
          </div>
          <p className="text-[13px] text-[#5a5a6b] mt-1">{dataset.description}</p>
        </div>
      </div>

      {/* Source info */}
      <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg px-5 py-3 mb-6 flex gap-8 text-[12px]">
        <div>
          <span className="text-[#4a4a58]">Source</span>
          <p className="text-[#8a8a9b] font-mono mt-0.5">{dataset.source_type}</p>
        </div>
        <div>
          <span className="text-[#4a4a58]">Bucket</span>
          <p className="text-[#8a8a9b] font-mono mt-0.5">{(dataset.source_config as Record<string, string>).bucket || '—'}</p>
        </div>
        <div>
          <span className="text-[#4a4a58]">Pattern</span>
          <p className="text-[#8a8a9b] font-mono mt-0.5 max-w-sm truncate">{(dataset.source_config as Record<string, string>).prefix_pattern || '—'}</p>
        </div>
      </div>

      {/* Folder / Schema selectors */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative">
          <select
            value={selectedFolderId || ''}
            onChange={(e) => {
              setSelectedFolderId(e.target.value);
              setSelectedSchemaId(null);
            }}
            className="appearance-none bg-[#12121e] border border-[#1a1a25] rounded-lg pl-3 pr-8 py-2 text-[13px] text-white cursor-pointer hover:border-[#2a2a35] transition-colors"
          >
            {folders?.map((f) => (
              <option key={f.id} value={f.id} className="bg-[#12121e]">{f.name}</option>
            ))}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-3 text-[#4a4a58] pointer-events-none" />
        </div>

        <span className="text-[#2a2a35]">/</span>

        <div className="relative">
          <select
            value={selectedSchemaId || ''}
            onChange={(e) => setSelectedSchemaId(e.target.value)}
            className="appearance-none bg-[#12121e] border border-[#1a1a25] rounded-lg pl-3 pr-8 py-2 text-[13px] text-white cursor-pointer hover:border-[#2a2a35] transition-colors"
          >
            {schemas?.map((s) => (
              <option key={s.id} value={s.id} className="bg-[#12121e]">
                v{s.major_version}.{s.minor_version} {!s.is_active ? '(inactive)' : ''}
              </option>
            ))}
          </select>
          <ChevronDown size={12} className="absolute right-2.5 top-3 text-[#4a4a58] pointer-events-none" />
        </div>

        {selectedSchema?.data_location_pattern && (
          <span className="text-[10px] font-mono text-[#3a3a48] bg-[#0d0d14] border border-[#1a1a25] px-2 py-1 rounded ml-2">
            {selectedSchema.data_location_pattern}
          </span>
        )}

        <div className="flex-1" />

        {hasChanges && (
          <button
            onClick={() => setShowBumpModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-[13px] font-medium rounded-lg hover:bg-blue-500 transition-colors"
          >
            <Save size={13} /> Save Changes
          </button>
        )}
      </div>

      {/* Schema fields table */}
      <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#1a1a25] text-left text-[11px] text-[#4a4a58] uppercase tracking-wider">
              <th className="py-2.5 px-3 font-medium">Field</th>
              <th className="py-2.5 px-3 font-medium">Type</th>
              <th className="py-2.5 px-3 font-medium text-center">Null</th>
              <th className="py-2.5 px-3 font-medium">Description</th>
              <th className="py-2.5 px-3 font-medium">Security</th>
            </tr>
          </thead>
          <tbody>
            {editableFields.map((field, i) => (
              <EditableFieldRow key={field.id} field={field} onChange={(f) => updateField(i, f)} />
            ))}
            {editableFields.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-[13px] text-[#3a3a48]">
                  No fields defined
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showBumpModal && <VersionBumpModal onSave={handleSaveVersion} onCancel={() => setShowBumpModal(false)} />}
    </div>
  );
}
