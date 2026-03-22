import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchFolder } from '../api/folders';
import { fetchSchemas } from '../api/schemas';
import { ArrowLeft, FileCode } from 'lucide-react';

export default function FolderDetailPage() {
  const { id, fid } = useParams<{ id: string; fid: string }>();
  const { data: folder } = useQuery({ queryKey: ['folder', fid], queryFn: () => fetchFolder(fid!) });
  const { data: schemas } = useQuery({ queryKey: ['schemas', fid], queryFn: () => fetchSchemas(fid!) });

  if (!folder) return <div className="text-gray-500">Loading...</div>;

  return (
    <div>
      <Link to={`/datasets/${id}`} className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={14} /> Back to Dataset
      </Link>

      <h1 className="text-2xl font-bold text-gray-900 mb-1">{folder.name}</h1>
      {folder.description && <p className="text-gray-500 mb-6">{folder.description}</p>}

      <h2 className="text-lg font-semibold text-gray-900 mb-3">Schema Versions</h2>
      <div className="grid gap-3">
        {schemas?.map((schema) => (
          <Link
            key={schema.id}
            to={`/schemas/${schema.id}`}
            className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4 hover:border-blue-300 transition-colors"
          >
            <div className="flex items-center gap-3">
              <FileCode className="text-purple-500" size={18} />
              <div>
                <h3 className="font-medium text-gray-900">
                  v{schema.major_version}.{schema.minor_version}
                  {!schema.is_active && <span className="ml-2 text-xs text-gray-400">(inactive)</span>}
                </h3>
                {schema.description && <p className="text-xs text-gray-500">{schema.description}</p>}
              </div>
            </div>
            <div className="text-sm text-gray-400">
              {schema.field_count} fields
              {schema.data_location_pattern && (
                <span className="ml-3 font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">
                  {schema.data_location_pattern.slice(0, 40)}...
                </span>
              )}
            </div>
          </Link>
        ))}
        {schemas?.length === 0 && <p className="text-gray-400 text-sm">No schema versions yet</p>}
      </div>
    </div>
  );
}
