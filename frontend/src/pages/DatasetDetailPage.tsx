import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchDataset } from '../api/datasets';
import { fetchFolders } from '../api/folders';
import { Folder as FolderIcon, ChevronRight, ArrowLeft } from 'lucide-react';

export default function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: dataset } = useQuery({ queryKey: ['dataset', id], queryFn: () => fetchDataset(id!) });
  const { data: folders } = useQuery({ queryKey: ['folders', id], queryFn: () => fetchFolders(id!) });

  if (!dataset) return <div className="text-gray-500">Loading...</div>;

  return (
    <div>
      <Link to="/datasets" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={14} /> Back to Datasets
      </Link>

      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-2xl font-bold text-gray-900">{dataset.name}</h1>
          <span className="text-sm text-gray-400 bg-gray-100 px-3 py-1 rounded-full">
            v{dataset.current_major_version}.{dataset.current_minor_version}
          </span>
        </div>
        <p className="text-gray-500 mb-4">{dataset.description}</p>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Source Type</span>
            <p className="font-medium text-gray-700">{dataset.source_type}</p>
          </div>
          <div>
            <span className="text-gray-400">Bucket</span>
            <p className="font-medium text-gray-700">{(dataset.source_config as Record<string,string>).bucket}</p>
          </div>
          <div>
            <span className="text-gray-400">Flags</span>
            <div className="flex gap-1 mt-1">
              {dataset.is_pii && <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">PII</span>}
              {dataset.is_financial && <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-xs">Financial</span>}
              {!dataset.is_pii && !dataset.is_financial && <span className="text-gray-400">None</span>}
            </div>
          </div>
        </div>
      </div>

      <h2 className="text-lg font-semibold text-gray-900 mb-3">Folders ({folders?.length || 0})</h2>
      <div className="grid gap-3">
        {folders?.map((folder) => (
          <Link
            key={folder.id}
            to={`/datasets/${id}/folders/${folder.id}`}
            className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4 hover:border-blue-300 transition-colors"
          >
            <div className="flex items-center gap-3">
              <FolderIcon className="text-yellow-500" size={18} />
              <div>
                <h3 className="font-medium text-gray-900">{folder.name}</h3>
                {folder.description && <p className="text-xs text-gray-500">{folder.description}</p>}
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <span>{folder.schema_count} schemas</span>
              <ChevronRight size={16} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
