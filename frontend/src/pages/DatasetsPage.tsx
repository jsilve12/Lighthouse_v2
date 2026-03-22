import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchDatasets } from '../api/datasets';
import { Database, Shield, DollarSign, Search, ChevronRight } from 'lucide-react';

export default function DatasetsPage() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useQuery({
    queryKey: ['datasets', search],
    queryFn: () => fetchDatasets(1, 50, search || undefined),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold text-white">Datasets</h1>
          <p className="text-[13px] text-[#6b6b7b] mt-1">Manage data sources and schemas</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-2.5 text-[#4a4a58]" size={14} />
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 pr-4 py-2 bg-[#12121e] border border-[#1a1a25] rounded-lg text-[13px] text-white placeholder-[#4a4a58] focus:border-blue-500/50 focus:bg-[#14142a] transition-colors w-56"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="text-[#4a4a58] text-sm">Loading...</div>
      ) : (
        <div className="space-y-2">
          {data?.items.map((dataset) => (
            <Link
              key={dataset.id}
              to={`/datasets/${dataset.id}`}
              className="group flex items-center justify-between bg-[#0d0d14] border border-[#1a1a25] rounded-lg px-5 py-4 hover:border-[#2a2a3a] hover:bg-[#0f0f1a] transition-all duration-200"
            >
              <div className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-md bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                  <Database className="text-blue-400" size={14} />
                </div>
                <div>
                  <div className="flex items-center gap-2.5">
                    <h3 className="text-[14px] font-medium text-white">{dataset.name}</h3>
                    <span className="text-[10px] font-mono text-[#4a4a58] bg-[#12121e] px-1.5 py-0.5 rounded">
                      v{dataset.current_major_version}.{dataset.current_minor_version}
                    </span>
                  </div>
                  <p className="text-[12px] text-[#5a5a6b] mt-0.5 max-w-md truncate">{dataset.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {dataset.is_pii && (
                  <span className="flex items-center gap-1 text-[10px] text-red-400 bg-red-500/10 border border-red-500/20 px-1.5 py-0.5 rounded">
                    <Shield size={9} /> PII
                  </span>
                )}
                {dataset.is_financial && (
                  <span className="flex items-center gap-1 text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded">
                    <DollarSign size={9} /> FIN
                  </span>
                )}
                <span className="text-[11px] text-[#4a4a58]">{dataset.folder_count} folders</span>
                <span className="text-[11px] text-[#3a3a48] font-mono">{dataset.source_type}</span>
                <ChevronRight size={14} className="text-[#2a2a35] group-hover:text-[#4a4a58] transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
