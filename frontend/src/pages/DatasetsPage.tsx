import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchDatasets } from '../api/datasets';
import { Database, Shield, DollarSign, Search } from 'lucide-react';

export default function DatasetsPage() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useQuery({
    queryKey: ['datasets', search],
    queryFn: () => fetchDatasets(1, 50, search || undefined),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Datasets</h1>
        <div className="relative">
          <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
          <input
            type="text"
            placeholder="Search datasets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="text-gray-500">Loading...</div>
      ) : (
        <div className="grid gap-4">
          {data?.items.map((dataset) => (
            <Link
              key={dataset.id}
              to={`/datasets/${dataset.id}`}
              className="block bg-white rounded-lg border border-gray-200 p-5 hover:border-blue-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <Database className="text-blue-500" size={20} />
                  <div>
                    <h3 className="font-semibold text-gray-900">{dataset.name}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">{dataset.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {dataset.is_pii && (
                    <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-medium flex items-center gap-1">
                      <Shield size={12} /> PII
                    </span>
                  )}
                  {dataset.is_financial && (
                    <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-xs font-medium flex items-center gap-1">
                      <DollarSign size={12} /> Financial
                    </span>
                  )}
                  <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                    v{dataset.current_major_version}.{dataset.current_minor_version}
                  </span>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
                <span>{dataset.source_type}</span>
                <span>{dataset.folder_count} folders</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
