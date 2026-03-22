import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchSchema } from '../api/schemas';
import { SecurityBadge } from '../components/common/StatusBadge';
import { ArrowLeft } from 'lucide-react';
import type { SchemaField } from '../types/schema';

function FieldRow({ field, depth = 0 }: { field: SchemaField; depth?: number }) {
  return (
    <>
      <tr className="border-t border-gray-100 hover:bg-gray-50">
        <td className="py-2 px-3 text-sm" style={{ paddingLeft: `${depth * 24 + 12}px` }}>
          <span className="font-mono text-gray-900">{field.name}</span>
          {field.array_element && <span className="ml-1 text-xs text-gray-400">[]</span>}
        </td>
        <td className="py-2 px-3 text-sm text-gray-600">{field.field_type}</td>
        <td className="py-2 px-3 text-sm text-center">{field.nullable ? 'Yes' : 'No'}</td>
        <td className="py-2 px-3 text-sm text-gray-500">{field.description || '-'}</td>
        <td className="py-2 px-3">
          <div className="flex gap-1">
            {field.is_pii && <SecurityBadge type="pii" />}
            {field.is_financial && <SecurityBadge type="financial" />}
            {field.is_encrypted && <SecurityBadge type="encrypted" />}
          </div>
        </td>
      </tr>
      {field.children?.map((child) => (
        <FieldRow key={child.id} field={child} depth={depth + 1} />
      ))}
    </>
  );
}

export default function SchemaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: schema } = useQuery({ queryKey: ['schema', id], queryFn: () => fetchSchema(id!) });

  if (!schema) return <div className="text-gray-500">Loading...</div>;

  return (
    <div>
      <button onClick={() => window.history.back()} className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={14} /> Back
      </button>

      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          Schema v{schema.major_version}.{schema.minor_version}
        </h1>
        {schema.description && <p className="text-gray-500 mb-3">{schema.description}</p>}
        {schema.data_location_pattern && (
          <div className="text-sm">
            <span className="text-gray-400">Location pattern: </span>
            <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">{schema.data_location_pattern}</code>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 text-left text-xs text-gray-500 uppercase">
            <tr>
              <th className="py-3 px-3">Field Name</th>
              <th className="py-3 px-3">Type</th>
              <th className="py-3 px-3 text-center">Nullable</th>
              <th className="py-3 px-3">Description</th>
              <th className="py-3 px-3">Security</th>
            </tr>
          </thead>
          <tbody>
            {schema.fields?.map((field) => (
              <FieldRow key={field.id} field={field} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
